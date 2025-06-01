using System.Text.Json.Serialization;

namespace Cardinal.EmbedingProcessor.Dtos;

public class QdrantPayload
{
    [JsonPropertyName("taskId")]
    public required Guid TaskId { get; set; }
    
    [JsonPropertyName("userId")]
    public required Guid UserId { get; set; }
    
    [JsonPropertyName("tag")]
    public required string Tag { get; set; }
    
    [JsonPropertyName("success_count")]
    public int SuccessCount { get; set; } = 0;

    [JsonPropertyName("fail_count")]
    public int FailCount { get; set; } = 0;
} 