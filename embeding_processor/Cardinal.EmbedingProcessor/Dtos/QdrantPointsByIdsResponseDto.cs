using System.Text.Json.Serialization;

namespace Cardinal.EmbedingProcessor.Dtos;

// Represents the structure returned by Qdrant when fetching points by IDs
// POST /collections/{collection_name}/points with body { "ids": [...] }
public class QdrantPointsByIdsResponseDto
{
    [JsonPropertyName("result")] 
    public QdrantPointResultDto[] Result { get; set; } = [];

    // We can ignore status and time for now, or add them if needed.
}

public class QdrantPointResultDto
{
    public Guid Id { get; set; }
    public float[] Vector { get; set; }
    public QdrantPayload Payload { get; set; }
} 