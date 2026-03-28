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
        var rb = modelBuilder.Entity<Recommendation>();
        rb.HasKey(p => p.Id);
        rb.HasIndex(p => p.TaskId);
    }
}