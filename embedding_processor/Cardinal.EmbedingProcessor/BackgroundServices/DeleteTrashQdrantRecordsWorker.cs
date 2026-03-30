using System.Text;
using Dapper;
using Microsoft.Data.SqlClient;
using Newtonsoft.Json;
using Npgsql;

namespace Cardinal.EmbedingProcessor.BackgroundServices;

public class DeleteTrashQdrantRecordsWorker(IServiceProvider serviceProvider, ILogger<DeleteTrashQdrantRecordsWorker> logger) : BackgroundService
{
    #region Private DTOs
    private record GetPointsResult([JsonProperty("points")]Point[]  Points);
    private record Point([JsonProperty("id")]Guid Id, [JsonProperty("payload")]PointPayload Payload);
    private record PointPayload([JsonProperty("user_id")]Guid UserId);
    #endregion
    
    private readonly IServiceProvider _serviceProvider = serviceProvider;
    private readonly string _sqlQuery = "select id from \"public\".\"users\"";
    private readonly int _pauseBetweenExecutionsMinutes = 30;

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        while (stoppingToken.IsCancellationRequested == false)
        {
            try
            {
                var httpClientFactory = _serviceProvider.GetRequiredService<IHttpClientFactory>();
                var config = _serviceProvider.GetRequiredService<IConfiguration>();

                var dbHost = config["ProdDb:Host"];
                var dbName = config["ProdDb:Db"];
                var dbUser = config["ProdDb:User"];
                var dbPassword = config["ProdDb:Password"];

                List<Guid> userIds;

                var connString =
                    $"Host={dbHost};Username={dbUser};Password={dbPassword};Database={dbName}";

                await using (var connection = new NpgsqlConnection(connString))
                {
                    await connection.OpenAsync(stoppingToken);
                    userIds = connection.Query<Guid>(_sqlQuery).ToList();
                }

                if (userIds.Count == 0)
                    continue;


                var client = httpClientFactory.CreateClient();
                var qdrantHost = config["Qdrant:Host"];
                var collectionName = config["Qdrant:CollectionName"];
                var apiKey = config["Qdrant:ApiKey"];

                if (!string.IsNullOrEmpty(apiKey))
                {
                    client.DefaultRequestHeaders.Add("api-key", apiKey);
                }

                var getDataUrl = $"{qdrantHost}/collections/{collectionName}/points/scroll";

                var response = await client.PostAsync(getDataUrl,
                    new StringContent(
                        JsonConvert.SerializeObject(new
                        {
                            with_payload = new[] { "user_id" },
                            with_vector = false
                        }), Encoding.UTF8, "application/json"
                    ), stoppingToken);

                if (response.IsSuccessStatusCode == false)
                    logger.LogError("Can't get Qdrant records: {StatusCode}", (int)response.StatusCode);

                var qdrantResponse =
                    JsonConvert.DeserializeObject<GetPointsResult>(
                        await response.Content.ReadAsStringAsync(stoppingToken));

                if (qdrantResponse == null || qdrantResponse.Points.Length == 0)
                    continue;

                var pointsToDelete = qdrantResponse.Points.Where(p => userIds.Contains(p.Payload.UserId) == false)
                    .ToList();

                var removeDataUrl = $"{qdrantHost}/collections/{collectionName}/points/delete?wait=true";

                response = await client.PostAsync(removeDataUrl,
                    new StringContent(
                        JsonConvert.SerializeObject(new
                        {
                            points = pointsToDelete.Select(p => p.Id).ToList()
                        }), Encoding.UTF8, "application/json"
                    ), stoppingToken);

                if (response.IsSuccessStatusCode == false)
                    logger.LogError("Can't delete TrashQdrant records: {StatusCode}", (int)response.StatusCode);
            }
            catch (Exception e)
            {
                logger.LogError($"Error in remove trash qdrant points process: {e.Message}. Stack Trace: {e.StackTrace}");
            }
            finally
            {
                await Task.Delay(TimeSpan.FromMinutes(_pauseBetweenExecutionsMinutes), stoppingToken);
            }
        }
    }
}