using System.Collections.Generic;
using System;
using System.Text;
using System.Text.RegularExpressions;
using System.Linq;

namespace Cardinal.EmbedingProcessor;

public static class TextSplitter
{
    private const int MaxTokens = 400 - 30; // words
    private const int MaxBytes = 1536 - 36; // extra

    private const string Space = " ";
    private const string Prefix = "query: ";

    private static readonly int PrefixByteCount = Encoding.UTF8.GetByteCount(Prefix);
    private static readonly int SpaceByteCount = Encoding.UTF8.GetByteCount(" ");

    public static List<string> SplitByTokensSlidingWindow(this string text, int stride = 128)
    {
        text = Regex.Replace(text, @"([\uD800-\uDBFF][\uDC00-\uDFFF]|[📝📌✏️✔️★☆]|[\p{C}])", "");
        text = Regex.Replace(text, @"\s+\n", "\n");
        text = Regex.Replace(text, @"\n{2,}", "\n\n");

        var tokens = text.Split((char[])null, StringSplitOptions.RemoveEmptyEntries);
        var blocks = new List<string>();

        int start = 0;
        while (start < tokens.Length)
        {
            var sb = new StringBuilder();
            sb.Append(Prefix);
            int byteCount = PrefixByteCount;
            int tokenCount = 0;

            int i = start;
            for (; i < tokens.Length; i++)
            {
                if (tokenCount >= MaxTokens)
                    break;

                string token = tokens[i];
                int tokenBytes = SpaceByteCount + Encoding.UTF8.GetByteCount(token);

                if (byteCount + tokenBytes > MaxBytes)
                    break;

                sb.Append(Space).Append(token);
                byteCount += tokenBytes;
                tokenCount++;
            }

            blocks.Add(sb.ToString());

            if (i == tokens.Length)
                break;

            int advance = i - start;
            if (advance == 0)
                advance = 1;

            start += Math.Min(stride, advance);
        }

        return blocks;
    }
}