using System.Text;
using Dapper;
using Microsoft.Data.SqlClient;
using Newtonsoft.Json;
using Npgsql;

namespace Cardinal.EmbedingProcessor.BackgroundServices;

public class DeleteTrashQdrantRecordsWorker(
    IServiceProvider serviceProvider,
    ILogger<DeleteTrashQdrantRecordsWorker> logger) : BackgroundService
{
    #region Private DTOs

    public class GetPointsResponse
    {
        [JsonProperty("result")] public GetPointsResult Result { get; set; }
    }

    public class GetPointsResult
    {
        [JsonProperty("points")] public List<Point> Points { get; set; } = new();
    }

    public class Point
    {
        [JsonProperty("id")] public Guid Id { get; set; }
        [JsonProperty("payload")] public PointPayload? Payload { get; set; }
    }

    public class PointPayload
    {
        [JsonProperty("user_id")] public Guid UserId { get; set; }
    }

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
                {
                    logger.LogInformation("No one user id found");
                    continue;
                }


                var client = httpClientFactory.CreateClient();
                var qdrantHost = config["Qdrant:Host"];
                var collectionName = config["Qdrant:CollectionName"];
                var apiKey = config["Qdrant:ApiKey"];

                if (!string.IsNullOrEmpty(apiKey))
                {
                    client.DefaultRequestHeaders.Add("api-key", apiKey);
                }

                var getDataUrl = $"{qdrantHost}/collections/{collectionName}/points/scroll";

                var body = JsonConvert.SerializeObject(new
                {
                    with_payload = new[] { "user_id" },
                    with_vector = false,
                    limit = int.MaxValue
                });

                logger.LogInformation("GetQdrantPoints body : {body}", body);

                var response = await client.PostAsync(getDataUrl,
                    new StringContent(
                        body, Encoding.UTF8, "application/json"
                    ), stoppingToken);

                if (response.IsSuccessStatusCode == false)
                {
                    logger.LogError("Can't get Qdrant records: {StatusCode}", (int)response.StatusCode);
                    continue;
                }

                var qdrantResponse =
                    JsonConvert.DeserializeObject<GetPointsResponse>(
                        await response.Content.ReadAsStringAsync(stoppingToken));

                if (qdrantResponse?.Result.Points is not { Count: > 0 })
                {
                    logger.LogError("Can't get Qdrant records: {StatusCode}. Body : {body}", (int)response.StatusCode,
                        await response.Content.ReadAsStringAsync(stoppingToken));
                    continue;
                }

                var pointsToDelete = qdrantResponse.Result.Points
                    .Where(p => userIds.Contains(p.Payload.UserId) == false)
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
                {
                    logger.LogError("Can't delete TrashQdrant records: {StatusCode}", (int)response.StatusCode);
                    continue;
                }
            }
            catch (Exception e)
            {
                logger.LogError(
                    $"Error in remove trash qdrant points process: {e.Message}. Stack Trace: {e.StackTrace}");
            }
            finally
            {
                logger.LogInformation("Run DeleteTrashQdrantRecords completed");
                await Task.Delay(TimeSpan.FromMinutes(_pauseBetweenExecutionsMinutes), stoppingToken);
            }
        }
    }
}