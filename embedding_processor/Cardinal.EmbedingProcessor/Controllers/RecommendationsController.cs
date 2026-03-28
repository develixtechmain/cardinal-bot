using Cardinal.EmbedingProcessor.Db;
using Cardinal.EmbedingProcessor.Db.Models;
using Microsoft.AspNetCore.Mvc;

[ApiController]
[Route("api/recommendation")]
public class RecommendationController : ControllerBase
{
    private readonly AppDbContext _db;
    public RecommendationController(AppDbContext db)
    {
        _db = db;
    }

    [HttpPost("confirm")]
    public async Task<IActionResult> Confirm([FromBody] ConfirmRecommendationRequest req)
    {
        var rec = new Recommendation
        {
            Id = req.RecommendationId,
            TaskId = req.TaskId,
            CreatedAt = DateTime.UtcNow
        };
        _db.Recommendations.Add(rec);
        await _db.SaveChangesAsync();
        return Ok();
    }
}

public class ConfirmRecommendationRequest
{
    public Guid RecommendationId { get; set; }
    public Guid TaskId { get; set; }
}