namespace Cardinal.EmbedingProcessor.Dtos;

public class SearchResponseItemDto
{
    public Guid TaskId { get; set; }
    public Guid UserId { get; set; }
    public float Score { get; set; }
    public List<SearchResponseTagDto> Tags { get; set; } = [];
} 