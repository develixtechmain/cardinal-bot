using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Cardinal.EmbedingProcessor.Migrations
{
    /// <inheritdoc />
    public partial class RemoveVectorsColumncs : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropColumn(
                name: "Vectors",
                table: "Recommendations");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<string>(
                name: "Vectors",
                table: "Recommendations",
                type: "text",
                nullable: false,
                defaultValue: "");
        }
    }
}
