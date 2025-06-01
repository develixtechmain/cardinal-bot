using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Filters;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using System;
using System.Threading.Tasks;

namespace Cardinal.EmbedingProcessor.Security
{
    public class ApiKeyAuthFilter : IAsyncAuthorizationFilter
    {
        private const string ApiKeyHeaderName = "X-Api-Key";
        private readonly IConfiguration _configuration;

        public ApiKeyAuthFilter(IConfiguration configuration)
        {
            _configuration = configuration;
        }

        public async Task OnAuthorizationAsync(AuthorizationFilterContext context)
        {
            var apiKeyInHeader = context.HttpContext.Request.Headers[ApiKeyHeaderName];
            var apiKeyFromConfig = _configuration["ApiKey"];

            if (string.IsNullOrEmpty(apiKeyInHeader) || string.IsNullOrEmpty(apiKeyFromConfig) || !apiKeyInHeader.Equals(apiKeyFromConfig))
            {
                context.Result = new UnauthorizedResult();
                return;
            }

            await Task.CompletedTask;
        }
    }
} 