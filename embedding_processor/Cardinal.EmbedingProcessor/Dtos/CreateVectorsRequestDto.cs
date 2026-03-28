namespace Cardinal.EmbedingProcessor.Dtos;

public class CreateVectorsRequestDto // Renamed to avoid conflict with a potential future model
{
    public string[] Tags { get; set; }
    public Guid TaskId { get; set; }
    public Guid UserId { get; set; }
}