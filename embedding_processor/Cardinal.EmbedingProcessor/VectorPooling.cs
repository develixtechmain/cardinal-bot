using System;
using System.Collections.Generic;
using System.Linq;

namespace Cardinal.EmbedingProcessor;

public static class VectorPooling
{
    /// <summary>
    /// Усредняет список векторов (mean pooling).
    /// </summary>
    public static float[] MeanPooling(IEnumerable<float[]> vectors)
    {
        var list = vectors.ToList();
        if (list.Count == 0) throw new ArgumentException("Список векторов пуст");
        int dim = list[0].Length;
        var result = new float[dim];
        foreach (var vec in list)
        {
            for (int i = 0; i < dim; i++)
                result[i] += vec[i];
        }
        for (int i = 0; i < dim; i++)
            result[i] /= list.Count;
        return result;
    }

    /// <summary>
    /// Максимизирует список векторов (max pooling).
    /// </summary>
    public static float[] MaxPooling(IEnumerable<float[]> vectors)
    {
        var list = vectors.ToList();
        if (list.Count == 0) throw new ArgumentException("Список векторов пуст");
        int dim = list[0].Length;
        var result = new float[dim];
        for (int i = 0; i < dim; i++)
            result[i] = float.MinValue;
        foreach (var vec in list)
        {
            for (int i = 0; i < dim; i++)
                result[i] = Math.Max(result[i], vec[i]);
        }
        return result;
    }
}