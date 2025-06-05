using System.Text.Json.Serialization;

namespace Cardinal.EmbedingProcessor.Dtos;

public class QdrantPayloadDto
{
    [JsonPropertyName("taskId")]
    public Guid TaskId { get; set; } // Changed to non-nullable Guid as it was 'required' previously
    
    [JsonPropertyName("userId")]
    public Guid UserId { get; set; } // Changed to non-nullable Guid
    
    [JsonPropertyName("tag")]
    public string Tag { get; set; } // Changed to non-nullable string
    
    [JsonPropertyName("success_count")]
    public int SuccessCount { get; set; } = 0;

    [JsonPropertyName("fail_count")]
    public int FailCount { get; set; } = 0;
} 