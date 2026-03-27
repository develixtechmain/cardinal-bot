using System.Net.Http.Json;

namespace Cardinal.EmbedingProcessor;

public static class QdrantInitializer
{
    public static async Task EnsureCollectionExists(IHttpClientFactory httpClientFactory, IConfiguration config)
    {
        var client = httpClientFactory.CreateClient();
        var qdrantHost = config["Qdrant:Host"];
        var collectionName = config["Qdrant:CollectionName"];
        var apiKey = config["Qdrant:ApiKey"];

        if (!string.IsNullOrEmpty(apiKey))
        {
            client.DefaultRequestHeaders.Add("api-key", apiKey);
        }

        var collectionUrl = $"{qdrantHost}/collections/{collectionName}";

        var response = await client.GetAsync(collectionUrl);

        if (!response.IsSuccessStatusCode)
        {
            var payload = new
            {
                vectors = new
                {
                    tag_embeddings = new
                    {
                        size = 768,
                        distance = "Cosine",
                        multivector_config = new
                        {
                            comparator = "max_sim"
                        }
                    }
                }
            };

            var createResponse = await client.PutAsJsonAsync(collectionUrl, payload);

            if (!createResponse.IsSuccessStatusCode)
            {
                var error = await createResponse.Content.ReadAsStringAsync();
                throw new Exception($"Failed to create Qdrant collection: {error}");
            }
        }
    }
}
