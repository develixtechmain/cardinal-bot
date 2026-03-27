using System.Text.Json.Serialization;

namespace Cardinal.EmbedingProcessor.Dtos;

public class QdrantSearchResponse
{
    [JsonPropertyName("result")]
    public QdrantResult Result { get; set; }
}

public class QdrantResult
{
    [JsonPropertyName("points")]
    public QdrantPointDto[] Points { get; set; }
}