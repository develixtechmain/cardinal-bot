using System.Collections.Generic;
using System;
using System.Linq;

namespace Cardinal.EmbedingProcessor;

public static class TextSplitter
{
    /// <summary>
    /// Грубо разбивает текст на чанки по "токенам" (словам через пробел) с overlap.
    /// </summary>
    /// <param name="text">Входной текст</param>
    /// <param name="windowSize">Размер окна в "токенах" (по умолчанию 256)</param>
    /// <param name="stride">Шаг окна в "токенах" (по умолчанию 128)</param>
    /// <returns>Список чанков-строк</returns>
    public static List<string> SplitByTokensSlidingWindow(this string text, int windowSize = 256, int stride = 128)
    {
        var tokens = text.Split((char[])null, StringSplitOptions.RemoveEmptyEntries);
        var tokenCount = tokens.Length;
        var chunks = new List<string>();

        for (int start = 0; start < tokenCount; start += stride)
        {
            int end = Math.Min(start + windowSize, tokenCount);
            var chunkTokens = tokens.Skip(start).Take(end - start);
            string chunk = string.Join(" ", chunkTokens);
            chunks.Add(chunk);
            if (end == tokenCount) break;
        }
        return chunks;
    }
}