# Используем официальный образ ASP.NET Core SDK для сборки
FROM mcr.microsoft.com/dotnet/sdk:9.0 AS build
WORKDIR /src

# Копируем .csproj и восстанавливаем зависимости
COPY ["Cardinal.EmbedingProcessor/Cardinal.EmbedingProcessor.csproj", "Cardinal.EmbedingProcessor/"]
# Можно скопировать .sln и NuGet.config, если они есть и нужны для восстановления
# COPY ["Cardinal.EmbedingProcessor.sln", "./"]
# COPY ["NuGet.config", "./"]
RUN dotnet restore "Cardinal.EmbedingProcessor/Cardinal.EmbedingProcessor.csproj"

# Копируем остальной исходный код проекта
COPY . .
WORKDIR "/src/Cardinal.EmbedingProcessor"
RUN dotnet build "Cardinal.EmbedingProcessor.csproj" -c Release -o /app/build

# Публикуем приложение
FROM build AS publish
RUN dotnet publish "Cardinal.EmbedingProcessor.csproj" -c Release -o /app/publish /p:UseAppHost=false

# Используем официальный образ ASP.NET Core runtime для запуска приложения
FROM mcr.microsoft.com/dotnet/aspnet:9.0 AS final
WORKDIR /app
COPY --from=publish /app/publish .

# Устанавливаем переменные окружения для ASP.NET Core
ENV ASPNETCORE_URLS=http://+:8080
# ASPNETCORE_ENVIRONMENT можно установить в docker-compose.yml

# Открываем порт, который слушает приложение
EXPOSE 8080
LABEL loki.include=true loki.service.name=embeddings_processor

# Запускаем приложение
ENTRYPOINT ["dotnet", "Cardinal.EmbedingProcessor.dll"] 