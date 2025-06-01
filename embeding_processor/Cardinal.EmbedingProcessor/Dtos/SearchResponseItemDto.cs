namespace Cardinal.EmbedingProcessor.Dtos;

public class SearchResponseItemDto
{
    public Guid TaskId { get; set; }
    public List<SearchResponseTagDto> Tags { get; set; } = [];
} 