using System.Text.Json.Serialization;

namespace Cardinal.EmbedingProcessor.Dtos;

public class QdrantSearchResponse
{
    [JsonPropertyName("result")]
    public QdrantPointDto[] Result { get; set; }
} 