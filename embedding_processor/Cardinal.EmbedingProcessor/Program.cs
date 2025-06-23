using Cardinal.EmbedingProcessor;
using Cardinal.EmbedingProcessor.Db;
using Cardinal.EmbedingProcessor.Security;
using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
// Learn more about configuring OpenAPI at https://aka.ms/aspnet/openapi
builder.Services.AddOpenApi();

// Регистрируем ApiKeyAuthFilter
builder.Services.AddScoped<ApiKeyAuthFilter>();
builder.Services.AddSingleton<VectorPooler>();

builder.Services.AddControllers(options =>
{
    options.Filters.Add<ApiKeyAuthFilter>(); // Применяем фильтр глобально
});
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

builder.Services.AddDbContextPool<AppDbContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("Postgres")));

builder.Services.AddHttpClient(); 

var app = builder.Build();

var scope = app.Services.CreateScope();
var ctx = scope.ServiceProvider.GetRequiredService<AppDbContext>();

await ctx.Database.MigrateAsync();

app.UseSwagger();
app.UseSwaggerUI();
app.MapControllers();
app.Run();
