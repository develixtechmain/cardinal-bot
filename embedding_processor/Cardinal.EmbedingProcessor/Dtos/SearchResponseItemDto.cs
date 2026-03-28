namespace Cardinal.EmbedingProcessor.Dtos;

public class SearchResponseItemDto
{
    public Guid TaskId { get; set; }
    public Guid UserId { get; set; }
    public double Score { get; set; }
}