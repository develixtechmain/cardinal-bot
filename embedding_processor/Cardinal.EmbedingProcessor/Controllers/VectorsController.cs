using Cardinal.EmbedingProcessor.Dtos;
using Microsoft.AspNetCore.Mvc;
using Newtonsoft.Json;

namespace Cardinal.EmbedingProcessor.Controllers;

[ApiController]
[Route("api/vectors")]
public class VectorsController : ControllerBase
{
    private readonly IHttpClientFactory _http;
    private readonly IConfiguration _config;

    public VectorsController(IHttpClientFactory http, IConfiguration config)
    {
        _http = http;
        _config = config;
    }

    [HttpPost("tags")]
    public async Task<IActionResult> CreateTagVectors([FromBody] CreateTagVectorsRequestDto req)
    {
        var embeddingUrl = _config["EmbeddingsApi:Host"] + "/embed";

        var tasks = req.Tags.Select(async p =>
        {
            var client = _http.CreateClient();
            var response = await client.PostAsJsonAsync(embeddingUrl, new { inputs = new[] { p } });
            var embeddingData = await response.Content.ReadFromJsonAsync<float[][]>();
            return new
            {
                Tag = p,
                Vector = embeddingData![0]
            };
        }).ToList();

        var results = await Task.WhenAll(tasks);
        
        var qdrantPointsToCreate = results.Select(vec => new 
        {
            id = Guid.NewGuid(),
            vector = vec.Vector,
            payload = new QdrantPayload { TaskId = req.TaskId, UserId = req.UserId, Tag = vec.Tag }
        }).ToArray();

        var qdrantClient = _http.CreateClient();
        var qdrantCollectionName = _config["Qdrant:CollectionName"];
        var qdrantUrl = $"{_config["Qdrant:Host"]}/collections/{qdrantCollectionName}/points";
        var qdrantApiKey = _config["Qdrant:ApiKey"];

        if (!string.IsNullOrEmpty(qdrantApiKey))
        {
            qdrantClient.DefaultRequestHeaders.Add("api-key", qdrantApiKey);
        }

        var qdrantResp = await qdrantClient.PutAsJsonAsync(qdrantUrl, new { points = qdrantPointsToCreate });
        if (!qdrantResp.IsSuccessStatusCode)
            return StatusCode(500, "Qdrant insert error");

        return Ok(qdrantPointsToCreate.Select(x => x.id));
    }
    
    [HttpDelete("by-task/{taskId}")]
    public async Task<IActionResult> DeleteByTask(Guid taskId)
    {
        var qdrantClient = _http.CreateClient();
        var qdrantCollectionName = _config["Qdrant:CollectionName"];
        var qdrantUrl = $"{_config["Qdrant:Host"]}/collections/{qdrantCollectionName}/points/delete";
        var qdrantApiKey = _config["Qdrant:ApiKey"];

        if (!string.IsNullOrEmpty(qdrantApiKey))
        {
            qdrantClient.DefaultRequestHeaders.Add("api-key", qdrantApiKey);
        }

        var filter = new
        {
            filter = new
            {
                must = new[]
                {
                    new { key = "taskId", match = new { value = taskId.ToString() } }
                }
            }
        };
        var resp = await qdrantClient.PostAsJsonAsync(qdrantUrl, filter);
        if (!resp.IsSuccessStatusCode)
            return StatusCode(500, "Qdrant delete error");

        return Ok("Deleted");
    }

    [HttpPost("search")]
    public async Task<ActionResult<List<SearchResponseItemDto>>> Search([FromBody] SearchMessageRequest req)
    {
        var embedClient = _http.CreateClient();
        var embeddingUrl = _config["EmbeddingsApi:Host"] + "/embed";
        var embeddingResp = await embedClient.PostAsJsonAsync(embeddingUrl, new { inputs = new[] { req.Message } });
        if (!embeddingResp.IsSuccessStatusCode)
            return StatusCode(500, "Embedding service error");
        var embeddingData = await embeddingResp.Content.ReadFromJsonAsync<float[][]>();
        if (embeddingData == null) return StatusCode(500, "No embedding data");

        var qdrantClient = _http.CreateClient();
        var qdrantCollectionName = _config["Qdrant:CollectionName"];
        var qdrantUrl = $"{_config["Qdrant:Host"]}/collections/{qdrantCollectionName}/points/search";
        var qdrantApiKey = _config["Qdrant:ApiKey"];

        if (!string.IsNullOrEmpty(qdrantApiKey))
        {
            qdrantClient.DefaultRequestHeaders.Add("api-key", qdrantApiKey);
        }

        var searchBody = new
        {
            vector = embeddingData[0],
            top = _config.GetValue<int>("Search:TopN", 1000),
            with_payload = true,
            score_threshold = _config.GetValue<double>("Search:ScoreThreshold", 0.85)
        };
        var qdrantResp = await qdrantClient.PostAsJsonAsync(qdrantUrl, searchBody);
        if (!qdrantResp.IsSuccessStatusCode)
            return StatusCode(500, "Qdrant search error");

        var qdrantResult = await qdrantResp.Content.ReadFromJsonAsync<QdrantSearchResponse>(); 
        if (qdrantResult == null || qdrantResult.Result == null) return StatusCode(500, "No Qdrant result or empty result array");
        
        var alpha = _config.GetValue<double>("Search:BayesianAlpha", 1.0);
        var beta = _config.GetValue<double>("Search:BayesianBeta", 1.0);
        var minGroupScoreSumThreshold = _config.GetValue<double>("Search:MinGroupScoreSumThreshold", 0.6);

        var groupedAndFiltered = qdrantResult.Result 
            .Select(x => 
            {
                var bayesianWeight = (alpha + x.Payload.SuccessCount) / (alpha + beta + x.Payload.SuccessCount + x.Payload.FailCount);
                var combinedScore = x.Score * bayesianWeight; 
                return new
                {
                    Point = x, 
                    TaskId = x.Payload.TaskId, 
                    UserId = x.Payload.UserId,
                    CombinedScore = combinedScore,
                    Text = x.Payload.Tag
                };
            })
            .GroupBy(x => x.TaskId) 
            .Select(g => new
            {
                TaskId = g.Key,
                UserId = g.First().UserId,
                Score = g.Select(p => p.CombinedScore).Max(),
                Tags = g.Select(x => new SearchResponseTagDto { Id = x.Point.Id, Text = x.Text}).ToList(), 
                SumOfCombinedScores = g.Sum(x => x.CombinedScore),
            })
            .Where(g => g.SumOfCombinedScores > minGroupScoreSumThreshold) 
            .Select(g => new SearchResponseItemDto 
            {
                TaskId = g.TaskId,
                UserId = g.UserId,
                Score = (float)g.Score,
                Tags = g.Tags
            })
            .ToList();

        return Ok(groupedAndFiltered);
    }
}