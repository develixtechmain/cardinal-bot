using System.Text.Json.Serialization;
using Cardinal.EmbedingProcessor.Db;
using Cardinal.EmbedingProcessor.Db.Models;
using Cardinal.EmbedingProcessor.Dtos;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace Cardinal.EmbedingProcessor.Controllers;

[ApiController]
[Route("api/learning")]
public class LearningController : ControllerBase
{
    private readonly AppDbContext _dbContext;
    private readonly IHttpClientFactory _httpFactory;
    private readonly IConfiguration _config;

    public LearningController(AppDbContext dbContext, IHttpClientFactory httpFactory, IConfiguration config)
    {
        _dbContext = dbContext;
        _httpFactory = httpFactory;
        _config = config;
    }

    [HttpPatch("{recommendationId}/success")]
    public async Task<IActionResult> MarkSuccess(Guid recommendationId)
    {
        var recommendation = await _dbContext.Recommendations.FirstOrDefaultAsync(r => r.Id == recommendationId);
        if (recommendation == null || recommendation.Vectors == null || !recommendation.Vectors.Any())
        {
            return NotFound("Recommendation not found or has no associated vectors.");
        }

        var qdrantClient = _httpFactory.CreateClient();
        var qdrantHost = _config["Qdrant:Host"];
        var collectionName = _config["Qdrant:CollectionName"];
        var qdrantApiKey = _config["Qdrant:ApiKey"];

        // Добавляем ключ API в заголовки, если он есть
        if (!string.IsNullOrEmpty(qdrantApiKey))
        {
            qdrantClient.DefaultRequestHeaders.Add("api-key", qdrantApiKey);
        }

        // 1. Fetch current points from Qdrant
        var fetchUrl = $"{qdrantHost}/collections/{collectionName}/points";
        var fetchBody = new { ids = recommendation.Vectors, with_payload = true, with_vector = false }; // Fetch by IDs with payload
        var fetchResponse = await qdrantClient.PostAsJsonAsync(fetchUrl, fetchBody);

        if (!fetchResponse.IsSuccessStatusCode)
        {
            return StatusCode((int)fetchResponse.StatusCode, await fetchResponse.Content.ReadAsStringAsync());
        }

        var qdrantResponse = await fetchResponse.Content.ReadFromJsonAsync<QdrantPointsByIdsResponseDto>(); // Use new DTO
        if (qdrantResponse == null || qdrantResponse.Result.Any() == false)
        {
            return StatusCode(500, "Failed to deserialize Qdrant response or empty result points.");
        }
        
        var pointsToUpdate = new List<QdrantSetPayloadOperation>();
        
        // 2. Prepare points for update
        foreach (var point in qdrantResponse.Result) // Iterate over qdrantResponse.Result.Points
        {
            var newPayload = new QdrantPayload
            {
                TaskId = point.Payload.TaskId,
                UserId = point.Payload.UserId,
                Tag = point.Payload.Tag,
                SuccessCount = point.Payload.SuccessCount + 1, // Increment success
                FailCount = point.Payload.FailCount 
            };
            
            pointsToUpdate.Add(new QdrantSetPayloadOperation { Points = [point.Id], Payload = newPayload });
        }
        
        if (!pointsToUpdate.Any()) 
        {
            return Ok("No points found in Qdrant for the given vector IDs or nothing to update.");
        }

        var requestObj = new QdrantBatchOperationRequest()
        {
            Operations = pointsToUpdate.Select(p => new QdrantBatchOperationItem
            {
                SetPayloadOperation = p
            }).ToList()
        };
        
        // 3. Update points in Qdrant (upsert operation)
        var updateUrl = $"{qdrantHost}/collections/{collectionName}/points/batch?wait=true"; 
        var updateResponse = await qdrantClient.PostAsJsonAsync(updateUrl, requestObj);

        if (!updateResponse.IsSuccessStatusCode)
        {
            return StatusCode((int)updateResponse.StatusCode, await updateResponse.Content.ReadAsStringAsync());
        }

        //4. Delete recommendation to avoid potential second call about this obj
        await _dbContext.Set<Recommendation>()
            .Where(p => p.Id == recommendationId)
            .ExecuteDeleteAsync();

        return Ok();
    }

    [HttpPatch("{recommendationId}/fail")]
    public async Task<IActionResult> MarkFail(Guid recommendationId)
    {
        var recommendation = await _dbContext.Recommendations.FirstOrDefaultAsync(r => r.Id == recommendationId);
        if (recommendation == null || recommendation.Vectors == null || !recommendation.Vectors.Any())
        {
            return NotFound("Recommendation not found or has no associated vectors.");
        }

        var qdrantClient = _httpFactory.CreateClient();
        var qdrantHost = _config["Qdrant:Host"];
        var collectionName = _config["Qdrant:CollectionName"];
        var qdrantApiKey = _config["Qdrant:ApiKey"];

        // Добавляем ключ API в заголовки, если он есть
        if (!string.IsNullOrEmpty(qdrantApiKey))
        {
            qdrantClient.DefaultRequestHeaders.Add("api-key", qdrantApiKey);
        }

        // 1. Fetch current points from Qdrant
        var fetchUrl = $"{qdrantHost}/collections/{collectionName}/points";
        var fetchBody = new { ids = recommendation.Vectors, with_payload = true, with_vector = true }; // Fetch by IDs with payload
        var fetchResponse = await qdrantClient.PostAsJsonAsync(fetchUrl, fetchBody);

        if (!fetchResponse.IsSuccessStatusCode)
        {
            return StatusCode((int)fetchResponse.StatusCode, await fetchResponse.Content.ReadAsStringAsync());
        }

        var qdrantResponse = await fetchResponse.Content.ReadFromJsonAsync<QdrantPointsByIdsResponseDto>(); // Use new DTO
        if (qdrantResponse == null || qdrantResponse.Result.Any() == false)
        {
            return StatusCode(500, "Failed to deserialize Qdrant response or empty result points.");
        }

        // 2. Prepare points for update
        var pointsToUpdate = new List<QdrantSetPayloadOperation>();
        foreach (var point in qdrantResponse.Result) // Iterate over qdrantResponse.Result.Points
        {
            var newPayload = new QdrantPayload
            {
                TaskId = point.Payload.TaskId,
                UserId = point.Payload.UserId,
                Tag = point.Payload.Tag,
                SuccessCount = point.Payload.SuccessCount,
                FailCount = point.Payload.FailCount + 1 // Increment fail
            };
            pointsToUpdate.Add(new QdrantSetPayloadOperation { Points = [point.Id], Payload = newPayload });
        }

        if (!pointsToUpdate.Any()) 
        {
            return Ok("No points found in Qdrant for the given vector IDs or nothing to update.");
        }

        var requestObj = new QdrantBatchOperationRequest()
        {
            Operations = pointsToUpdate.Select(p => new QdrantBatchOperationItem
            {
                SetPayloadOperation = p
            }).ToList()
        };
        
        // 3. Update points in Qdrant (upsert operation)
        var updateUrl = $"{qdrantHost}/collections/{collectionName}/points/batch?wait=true"; 
        var updateResponse = await qdrantClient.PostAsJsonAsync(updateUrl, requestObj);

        if (!updateResponse.IsSuccessStatusCode)
        {
            return StatusCode((int)updateResponse.StatusCode, await updateResponse.Content.ReadAsStringAsync());
        }
        
        //4. Delete recommendation to avoid potential second call about this obj
        await _dbContext.Set<Recommendation>()
            .Where(p => p.Id == recommendationId)
            .ExecuteDeleteAsync();
        
        return Ok();
    }
}

public class QdrantBatchOperationRequest
{
    [JsonPropertyName("operations")]
    public List<QdrantBatchOperationItem> Operations { get; set; } = [];
}

public class QdrantBatchOperationItem
{
    [JsonPropertyName("set_payload")]
    public QdrantSetPayloadOperation? SetPayloadOperation { get; set; }
}

public class QdrantSetPayloadOperation
{
    [JsonPropertyName("points")]
    public List<Guid> Points { get; set; } = [];
    
    [JsonPropertyName("payload")]
    public required QdrantPayload Payload { get; set; }
}