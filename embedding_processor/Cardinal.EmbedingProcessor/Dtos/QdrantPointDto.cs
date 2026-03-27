using System.Text.Json.Serialization;

namespace Cardinal.EmbedingProcessor.Dtos;

public class QdrantPointDto
{
    [JsonPropertyName("id")]
    public Guid Id { get; set; }

    [JsonPropertyName("version")]
    public int Version { get; set; }

    [JsonPropertyName("score")]
    public double Score { get; set; }

    [JsonPropertyName("payload")]
    public QdrantPayload Payload { get; set; }
}