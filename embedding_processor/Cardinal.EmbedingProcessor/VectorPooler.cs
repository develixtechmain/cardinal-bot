namespace Cardinal.EmbedingProcessor;

public class VectorPooler(IConfiguration configuration)
{
    public float[] PoolVectors(params float[][] vectors)
    {
        var mode = configuration["Search:PoolingMode"];

        if (string.IsNullOrEmpty(mode))
            throw new Exception("Polling mode is not set");

        switch (mode)
        {
            case "mean":
                return VectorPooling.MeanPooling(vectors);

            case "max":
                return VectorPooling.MaxPooling(vectors);

            default:
                throw new Exception("Unknown pooling type");
        }
    }
}