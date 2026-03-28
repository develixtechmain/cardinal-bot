using System.Text.Json.Serialization;
using Cardinal.EmbedingProcessor.Db;
using Cardinal.EmbedingProcessor.Db.Models;
using Cardinal.EmbedingProcessor.Dtos;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using System.Text.Json;
using System.Text;

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
        return await UpdateTaskCounters(recommendationId, incrementSuccess: true);
    }

    [HttpPatch("{recommendationId}/fail")]
    public async Task<IActionResult> MarkFail(Guid recommendationId)
    {
        return await UpdateTaskCounters(recommendationId, incrementSuccess: false);
    }

    private async Task<IActionResult> UpdateTaskCounters(Guid recommendationId, bool incrementSuccess)
    {
        var recommendation = await _dbContext.Recommendations.FirstOrDefaultAsync(r => r.Id == recommendationId);
        if (recommendation == null)
        {
            return NotFound("Recommendation not found or has no associated vectors.");
        }

        var taskId = recommendation.TaskId;

        var client = _httpFactory.CreateClient();
        var apiKey = _config["Qdrant:ApiKey"];
        if (!string.IsNullOrEmpty(apiKey)) client.DefaultRequestHeaders.Add("api-key", apiKey);

        var url = $"{_config["Qdrant:Host"]}/collections/{_config["Qdrant:CollectionName"]}/points/{taskId}";
        var resp = await client.GetAsync(url + "?with_payload=true");
        resp.EnsureSuccessStatusCode();
        var point = await resp.Content.ReadFromJsonAsync<JsonElement>();

        var payload = point.GetProperty("result").GetProperty("payload");
        var success = payload.GetProperty("success_count").GetInt32() + (incrementSuccess ? 1 : 0);
        var fail = payload.GetProperty("fail_count").GetInt32() + (incrementSuccess ? 0 : 1);

        var updatePayload = new
        {
            points = new[] { taskId },
            payload = new
            {
                success_count = success,
                fail_count = fail
            }
        };

        var updateResp = await client.PostAsJsonAsync($"{_config["Qdrant:Host"]}/collections/{_config["Qdrant:CollectionName"]}/points/payload", updatePayload);
        updateResp.EnsureSuccessStatusCode();
        return Ok();
    }
}