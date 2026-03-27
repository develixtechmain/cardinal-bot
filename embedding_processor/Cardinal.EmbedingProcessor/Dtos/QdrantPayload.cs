using System.Text.Json.Serialization;

namespace Cardinal.EmbedingProcessor.Dtos;

public class QdrantPayload
{
    [JsonPropertyName("task_id")]
    public required Guid TaskId { get; set; }

    [JsonPropertyName("user_id")]
    public required Guid UserId { get; set; }

    [JsonPropertyName("tags")]
    public required string[] Tags { get; set; }

    [JsonPropertyName("success_count")]
    public int SuccessCount { get; set; } = 0;

    [JsonPropertyName("fail_count")]
    public int FailCount { get; set; } = 0;
}