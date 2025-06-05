namespace Cardinal.EmbedingProcessor.Db.Models;

public class Recommendation
{
    public required Guid Id { get; set; }
    public required Guid TaskId { get; set; }
    public List<Guid> Vectors { get; set; } = [];
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
}