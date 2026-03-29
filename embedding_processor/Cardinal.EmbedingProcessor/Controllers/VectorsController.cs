using Cardinal.EmbedingProcessor.Dtos;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;
using Newtonsoft.Json;
using System.Text;

namespace Cardinal.EmbedingProcessor.Controllers;

[ApiController]
[Route("api/vectors")]
public class VectorsController : ControllerBase
{
    private readonly IHttpClientFactory _http;
    private readonly IConfiguration _config;
    private readonly VectorPooler _pooler;
    private readonly ILogger<VectorsController> _logger;

    private const string VectorName = "tag_embeddings";

    public VectorsController(IHttpClientFactory http, IConfiguration config, VectorPooler pooler, ILogger<VectorsController> logger)
    {
        _http = http;
        _config = config;
        _pooler = pooler;
        _logger = logger;
    }

    [HttpPost("tags")]
    public async Task<IActionResult> CreateOrUpdateTagVectors([FromBody] CreateVectorsRequestDto req)
    {
        if (req.Tags == null || !req.Tags.Any())
            return BadRequest("Tags array is empty");

        var embeddingUrl = _config["EmbeddingsApi:Host"] + "/embed";

        // Добавляем префикс "passage: " — обязательно для multilingual-e5!
        var inputsWithPrefix = req.Tags.Select(t => $"passage: {t}").ToArray();

        var client = _http.CreateClient();
        var response = await client.PostAsJsonAsync(embeddingUrl, new { inputs = inputsWithPrefix });
        response.EnsureSuccessStatusCode();

        var embeddings = await response.Content.ReadFromJsonAsync<float[][]>()
                         ?? throw new Exception("Empty embeddings response");

        var point = new
        {
            id = req.TaskId,
            vectors = new Dictionary<string, float[][]>
            {
                [VectorName] = embeddings
            },
            payload = new QdrantPayload
            {
                TaskId = req.TaskId,
                UserId = req.UserId,
                Tags = req.Tags,
                SuccessCount = 0,
                FailCount = 0,
            }
        };

        await UpsertPoints(new[] { point });

        return Ok(new { req.TaskId });
    }

    [HttpDelete("by-task/{taskId}")]
    public async Task<IActionResult> DeleteByTask(Guid taskId)
    {
        var qdrantClient = CreateQdrantClient();

        var deleteUrl = $"{_config["Qdrant:Host"]}/collections/{_config["Qdrant:CollectionName"]}/points/delete";

        var body = new
        {
            points = new[] { taskId }
        };

        var resp = await qdrantClient.PostAsJsonAsync(deleteUrl, body);
        if (!resp.IsSuccessStatusCode)
            return StatusCode(500, await resp.Content.ReadAsStringAsync());

        return Ok("Deleted");
    }

    [HttpPost("search")]
    public async Task<ActionResult<List<SearchResponseItemDto>>> Search([FromBody] SearchMessageRequest req)
    {
        var requestId = Guid.NewGuid();
        var split = req.Message.SplitByTokensSlidingWindow();
        var totalBlocks = split.Count;

        if (totalBlocks == 0)
        {
            _logger.LogWarning("Embed request {RequestId} | No blocks after splitting {Message}", requestId, req.Message);
            return Ok(new List<SearchResponseItemDto>());
        }

        var embedClient = _http.CreateClient();
        var embeddingUrl = _config["EmbeddingsApi:Host"] + "/embed";

        for (int i = 0; i < split.Count; i++)
        {
            var block = split[i];
            var charCount = block.Length;
            var wordCount = block.Split((char[])null, StringSplitOptions.RemoveEmptyEntries).Length;
            var byteSize = Encoding.UTF8.GetByteCount(JsonConvert.SerializeObject(block));

            _logger.LogInformation(
                "Embed request {RequestId} | Block={BlockIndex}/{BlocksTotal} | Chars={Chars} | Words={Words} | Bytes={Bytes}b",
                requestId,
                i + 1,
                totalBlocks,
                charCount,
                wordCount,
                byteSize
            );
        }

        var batchJson = new { inputs = split };
        var batchJsonString = JsonConvert.SerializeObject(batchJson);
        var totalByteSize = Encoding.UTF8.GetByteCount(batchJsonString);
        var totalCharCount = batchJsonString.Length;

        _logger.LogInformation(
            "Embed request {RequestId} | TotalBlocks={BlocksTotal} | TotalChars={TotalChars} | TotalBytes={TotalBytes}b",
            requestId,
            totalBlocks,
            totalCharCount,
            totalByteSize
        );


        var embeddingResp = await embedClient.PostAsJsonAsync(embeddingUrl, batchJson);
        if (embeddingResp.StatusCode == System.Net.HttpStatusCode.RequestEntityTooLarge)
        {
            _logger.LogWarning("Embed request {RequestId} | Payload too large (413). TotalBlocks={BlocksTotal} | TotalChars={TotalChars} | TotalBytes={TotalBytes}b",
            requestId,
            totalBlocks,
            totalCharCount,
            totalByteSize);
            return Ok(new List<SearchResponseItemDto>());
        }

        embeddingResp.EnsureSuccessStatusCode();

        var embeddingData = await embeddingResp.Content.ReadFromJsonAsync<float[][]>()
                            ?? throw new Exception("No embedding data");

        var pooledEmbedding = _pooler.PoolVectors(embeddingData);

        var qdrantClient = CreateQdrantClient();
        var searchUrl = $"{_config["Qdrant:Host"]}/collections/{_config["Qdrant:CollectionName"]}/points/query";

        var searchBody = new
        {
            query = pooledEmbedding,
            @using = VectorName,
            limit = _config.GetValue<int>("Search:TopN", 1000),
            with_payload = true,
            score_threshold = _config.GetValue<double>("Search:ScoreThreshold", 0.85)
        };

        _logger.LogInformation($"Search parameters: ScoreThreshold {_config.GetValue<double>("Search:ScoreThreshold", 0.85)}, TopN {_config.GetValue<int>("Search:TopN", 1000)}")

        var qdrantResp = await qdrantClient.PostAsJsonAsync(searchUrl, searchBody);
        qdrantResp.EnsureSuccessStatusCode();

        var qdrantResult = await qdrantResp.Content.ReadFromJsonAsync<QdrantSearchResponse>()
                           ?? throw new Exception("Empty Qdrant response");

        var alpha = _config.GetValue<double>("Search:BayesianAlpha", 1.0);
        var beta = _config.GetValue<double>("Search:BayesianBeta", 1.0);
        var minGroupScoreSumThreshold = _config.GetValue<double>("Search:MinGroupScoreSumThreshold", 0.6);

        var result = qdrantResult.Result.Points
            .Select(x =>
            {
                //  var bayesianWeight = (alpha + x.Payload.SuccessCount) / (alpha + beta + x.Payload.SuccessCount + x.Payload.FailCount);
                //  var combinedScore = x.Score * bayesianWeight;

                return new SearchResponseItemDto
                {
                    TaskId = x.Payload.TaskId,
                    UserId = x.Payload.UserId,
                    Score = x.Score,
                };
            })
            .Where(x => x.Score > minGroupScoreSumThreshold)
            .OrderByDescending(x => x.Score)
            .ToList();

        return Ok(result);
    }

    private HttpClient CreateQdrantClient()
    {
        var client = _http.CreateClient();
        var apiKey = _config["Qdrant:ApiKey"];
        if (!string.IsNullOrEmpty(apiKey))
            client.DefaultRequestHeaders.Add("api-key", apiKey);
        return client;
    }

    private async Task UpsertPoints(object[] points)
    {
        var client = CreateQdrantClient();
        var collection = _config["Qdrant:CollectionName"];
        var url = $"{_config["Qdrant:Host"]}/collections/{collection}/points";

        var body = new { points };
        var resp = await client.PutAsJsonAsync(url, body);
        resp.EnsureSuccessStatusCode();
    }
}