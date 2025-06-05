using Cardinal.EmbedingProcessor.Db.Models;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Storage.ValueConversion;

namespace Cardinal.EmbedingProcessor.Db;

public class AppDbContext : DbContext
{
    public DbSet<Recommendation> Recommendations { get; set; }

    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        var converter = new ValueConverter<List<Guid>, string>(
            v => string.Join(",", v),
            v => v.Split(',', StringSplitOptions.RemoveEmptyEntries).Select(Guid.Parse).ToList());

        var recommendationBuilder = modelBuilder.Entity<Recommendation>();

        recommendationBuilder.HasKey(p => p.Id);
        recommendationBuilder.HasIndex(p => p.TaskId);    
        
        recommendationBuilder
            .Property(r => r.Vectors)
            .HasConversion(converter);
    }
}