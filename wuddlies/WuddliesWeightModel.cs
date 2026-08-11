using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;

namespace Wuddlies.Unity
{
    public class WuddliesSafetensorsNameSource : INameSource
    {
        private const int BOS = 0;
        private const int EOS = 1;
        private const int CHAR_BASE = 2;

        private const int DIM_CULTURE = 8;
        private const int CULT_PROJ = 16;
        private const int PAR_PROJ = 16;

        private const double RICHNESS_FLOOR = 50.0;
        private const double POP_CLAMP = 0.12;
        private const double POP_ABSENT = 0.002;

        private static readonly string[] TYPES = { "given", "surname", "full" };
        private static readonly string[] GENDERS = { "U", "M", "F" };

        private static readonly Dictionary<string, double> ApproxPopM = new Dictionary<string, double>
        {
            { "CN", 1425 }, { "IN", 1440 }, { "US", 342 }, { "ID", 284 }, { "PK", 245 }, { "NG", 229 },
            { "BR", 217 }, { "BD", 174 }, { "RU", 144 }, { "MX", 130 }, { "ET", 129 }, { "JP", 123 },
            { "PH", 119 }, { "EG", 116 }, { "VN", 100 }, { "CD", 102 }, { "IR", 91 }, { "TR", 87 },
            { "DE", 84 }, { "TH", 72 }, { "GB", 68 }, { "TZ", 68 }, { "FR", 66 }, { "ZA", 63 }, { "IT", 59 },
            { "KE", 56 }, { "MM", 54 }, { "KR", 52 }, { "CO", 52 }, { "SD", 49 }, { "UG", 48 }, { "ES", 48 },
            { "AR", 46 }, { "DZ", 46 }, { "IQ", 46 }, { "AF", 42 }, { "CA", 39 }, { "MA", 38 }, { "PL", 37 },
            { "UA", 37 }, { "AO", 36 }, { "UZ", 35 }, { "MY", 34 }, { "PE", 34 }, { "GH", 34 }, { "YE", 34 },
            { "SA", 33 }, { "MZ", 33 }, { "NP", 31 }, { "MG", 30 }, { "CI", 29 }, { "CM", 29 }, { "VE", 28 },
            { "NE", 27 }, { "AU", 26 }, { "TW", 23 }, { "ML", 23 }, { "BF", 23 }, { "SY", 23 }, { "LK", 22 },
            { "KZ", 20 }, { "CL", 20 }, { "RO", 19 }, { "EC", 18 }, { "GT", 18 }, { "SN", 18 }, { "NL", 18 },
            { "TD", 18 }, { "SO", 18 }, { "KH", 17 }, { "ZW", 16 }, { "GN", 14 }, { "RW", 14 }, { "BJ", 14 },
            { "TN", 12 }, { "BE", 12 }, { "JO", 11 }, { "CU", 11 }, { "HT", 12 }, { "BO", 12 }, { "DO", 11 },
            { "SS", 11 }, { "AZ", 10 }, { "SE", 11 }, { "HU", 10 }, { "GR", 10 }, { "PT", 10 }, { "CZ", 11 },
            { "IL", 10 }, { "AE", 10 }, { "TJ", 10 }, { "PG", 10 }, { "AT", 9 }, { "CH", 9 }, { "TG", 9 },
            { "HN", 10 }, { "HK", 8 }, { "LA", 8 }, { "LY", 7 }, { "PY", 7 }, { "KG", 7 }, { "NI", 7 },
            { "RS", 7 }, { "TM", 7 }, { "BG", 6 }, { "LB", 6 }, { "DK", 6 }, { "FI", 6 }, { "SG", 6 },
            { "NO", 6 }, { "SK", 5 }, { "PS", 5 }, { "IE", 5 }, { "OM", 5 }, { "CR", 5 }, { "NZ", 5 },
            { "KW", 4 }, { "HR", 4 }, { "GE", 4 }, { "UY", 3 }, { "BA", 3 }, { "AM", 3 }, { "AL", 3 },
            { "MD", 3 }, { "LT", 3 }, { "QA", 3 }, { "MK", 2 }, { "SI", 2 }, { "LV", 2 }, { "BH", 2 },
            { "EE", 1 }, { "CY", 1 }, { "ME", 0.6 }, { "LU", 0.7 }, { "MT", 0.5 }, { "IS", 0.4 },
        };

        public List<string> Regions { get; private set; }

        private List<string> _chars;
        private Dictionary<string, int> _charToIdx;
        private List<double> _regionWeights;
        private List<int> _regionRichness;
        private List<double> _genderPrior;

        private int _vocab;
        private int _k;
        private int _dimChar;
        private int _dimRegion;
        private int _dimType;
        private int _dimGender;
        private int _dimOrigin;
        private int _hidden;

        private Tensor _ec;
        private Tensor _er;
        private Tensor _et;
        private Tensor _eg;
        private Tensor _eo;
        private Tensor _wc;
        private Tensor _wp;
        private Tensor _w1;
        private Tensor _b1;
        private Tensor _w2;
        private Tensor _b2;
        private Tensor _w3;
        private Tensor _b3;

        private WuddliesSafetensorsNameSource() { }

        public static WuddliesSafetensorsNameSource LoadFromFile(string path)
        {
            var bytes = File.ReadAllBytes(path);
            return LoadFromBytes(bytes);
        }

        public static WuddliesSafetensorsNameSource LoadFromBytes(byte[] raw)
        {
            if (raw == null || raw.Length < 8)
            {
                throw new InvalidDataException("invalid safetensors payload");
            }

            ulong hlen = BitConverter.ToUInt64(raw, 0);
            if (hlen == 0 || 8UL + hlen > (ulong)raw.Length)
            {
                throw new InvalidDataException("invalid safetensors header length");
            }

            string headerJson = Encoding.UTF8.GetString(raw, 8, (int)hlen);
            var parsed = MiniJson.Deserialize(headerJson) as Dictionary<string, object>;
            if (parsed == null)
            {
                throw new InvalidDataException("failed to parse safetensors header JSON");
            }

            if (!parsed.TryGetValue("__metadata__", out var metaObj))
            {
                throw new InvalidDataException("safetensors metadata missing");
            }

            var meta = metaObj as Dictionary<string, object>;
            if (meta == null)
            {
                throw new InvalidDataException("safetensors metadata malformed");
            }

            var model = new WuddliesSafetensorsNameSource();
            model.ReadMetadata(meta);

            int dataBase = 8 + (int)hlen;
            model._ec = ReadTensor(parsed, raw, dataBase, "Ec");
            model._er = ReadTensor(parsed, raw, dataBase, "Er");
            model._et = ReadTensor(parsed, raw, dataBase, "Et");
            model._eg = ReadTensor(parsed, raw, dataBase, "Eg");
            model._eo = ReadTensor(parsed, raw, dataBase, "Eo", optional: true) ?? Tensor.Zeros(new[] { 1, model._dimOrigin });
            model._wc = ReadTensor(parsed, raw, dataBase, "Wc", optional: true) ?? Tensor.Zeros(new[] { DIM_CULTURE, CULT_PROJ });
            model._wp = ReadTensor(parsed, raw, dataBase, "Wp", optional: true) ?? Tensor.Zeros(new[] { model._dimChar, PAR_PROJ });
            model._w1 = ReadTensor(parsed, raw, dataBase, "W1");
            model._b1 = ReadTensor(parsed, raw, dataBase, "b1");
            model._w2 = ReadTensor(parsed, raw, dataBase, "W2");
            model._b2 = ReadTensor(parsed, raw, dataBase, "b2");
            model._w3 = ReadTensor(parsed, raw, dataBase, "W3");
            model._b3 = ReadTensor(parsed, raw, dataBase, "b3");

            int dIn = model._k * model._dimChar + model._dimRegion + model._dimType + model._dimGender + model._dimOrigin + CULT_PROJ + PAR_PROJ;
            if (model._w1.Shape[0] < dIn)
            {
                var padded = Tensor.Zeros(new[] { dIn, model._w1.Shape[1] });
                int oldRows = model._w1.Shape[0];
                int cols = model._w1.Shape[1];
                for (int r = 0; r < oldRows; r++)
                {
                    int src = r * cols;
                    int dst = r * cols;
                    Array.Copy(model._w1.Data, src, padded.Data, dst, cols);
                }
                model._w1 = padded;
            }

            if (model._eo.Shape[0] <= 0)
            {
                model._eo = Tensor.Zeros(new[] { 1, model._dimOrigin });
            }

            if (model._genderPrior.Count != GENDERS.Length)
            {
                model._genderPrior = new List<double> { 0.0, 0.5, 0.5 };
            }

            return model;
        }

        public double[] RegionDrawWeights(WorldMix world)
        {
            int n = Regions.Count;
            var rich = new double[n];
            for (int i = 0; i < n; i++)
            {
                int rr = i < _regionRichness.Count ? _regionRichness[i] : 0;
                rich[i] = rr;
            }

            var voice = new double[n];
            for (int i = 0; i < n; i++)
            {
                voice[i] = Math.Min(1.0, rich[i] / RICHNESS_FLOOR);
            }

            var w = new double[n];
            if (world == WorldMix.Archive)
            {
                for (int i = 0; i < n; i++)
                {
                    w[i] = i < _regionWeights.Count ? _regionWeights[i] : 1.0;
                }
            }
            else if (world == WorldMix.Equal)
            {
                Array.Copy(voice, w, n);
            }
            else
            {
                var pop = new double[n];
                double sumPop = 0;
                for (int i = 0; i < n; i++)
                {
                    pop[i] = ApproxPopM.TryGetValue(Regions[i], out var p) ? p : 0.0;
                    sumPop += pop[i];
                }

                for (int i = 0; i < n; i++)
                {
                    double share = pop[i] > 0 ? pop[i] / Math.Max(sumPop, 1e-9) : POP_ABSENT;
                    w[i] = Math.Min(share, POP_CLAMP) * voice[i];
                }
            }

            double total = 0;
            for (int i = 0; i < n; i++) total += w[i];
            if (total <= 0)
            {
                for (int i = 0; i < n; i++) w[i] = 1.0;
                total = n;
            }

            for (int i = 0; i < n; i++) w[i] /= total;
            return w;
        }

        public string SampleGender(Rng64 rng)
        {
            double[] p = _genderPrior.ToArray();
            int idx = WeightedIndex(rng, p);
            return GENDERS[Math.Max(0, Math.Min(idx, GENDERS.Length - 1))];
        }

        public string SampleName(Rng64 rng, string region, NameType type, string gender, double temperature)
        {
            int regI;
            if (string.IsNullOrWhiteSpace(region))
            {
                var w = RegionDrawWeights(WorldMix.Archive);
                regI = WeightedIndex(rng, w);
            }
            else
            {
                regI = Regions.IndexOf(region);
                if (regI < 0)
                {
                    throw new ArgumentException("Unknown region for loaded weight: " + region);
                }
            }

            int typI = type == NameType.Given ? 0 : 1;
            int genI;
            if (string.IsNullOrWhiteSpace(gender))
            {
                if (type == NameType.Given)
                {
                    double[] p = _genderPrior.ToArray();
                    genI = WeightedIndex(rng, Normalize(p));
                }
                else
                {
                    genI = 0;
                }
            }
            else
            {
                genI = Array.IndexOf(GENDERS, gender);
                if (genI < 0) genI = 0;
            }

            int oriI = 0;
            var ctx = new int[_k];
            for (int i = 0; i < _k; i++) ctx[i] = BOS;
            var outChars = new List<char>();

            for (int step = 0; step < 24; step++)
            {
                var logits = Forward(ctx, regI, typI, genI, oriI);

                var z = new double[logits.Length];
                double t = Math.Max(temperature, 1e-4);
                for (int i = 0; i < logits.Length; i++) z[i] = logits[i] / t;
                z[BOS] = double.NegativeInfinity;
                if (outChars.Count < 2) z[EOS] = double.NegativeInfinity;

                double max = double.NegativeInfinity;
                for (int i = 0; i < z.Length; i++) if (z[i] > max) max = z[i];

                var p = new double[z.Length];
                double sum = 0;
                for (int i = 0; i < z.Length; i++)
                {
                    if (double.IsNegativeInfinity(z[i]))
                    {
                        p[i] = 0;
                    }
                    else
                    {
                        p[i] = Math.Exp(z[i] - max);
                    }
                    sum += p[i];
                }

                if (sum <= 0) break;
                for (int i = 0; i < p.Length; i++) p[i] /= sum;

                int nxt = WeightedIndex(rng, p);
                if (nxt == EOS) break;
                int cIdx = nxt - CHAR_BASE;
                if (cIdx < 0 || cIdx >= _chars.Count) break;
                string cs = _chars[cIdx];
                if (string.IsNullOrEmpty(cs)) continue;
                outChars.Add(cs[0]);

                for (int i = 0; i < _k - 1; i++) ctx[i] = ctx[i + 1];
                ctx[_k - 1] = nxt;
            }

            return new string(outChars.ToArray());
        }

        private float[] Forward(int[] ctx, int regI, int typI, int genI, int oriI)
        {
            int dIn = _w1.Shape[0];
            var x = new float[dIn];
            int off = 0;

            int ecCols = _ec.Shape[1];
            for (int i = 0; i < _k; i++)
            {
                int idx = ctx[i];
                int src = idx * ecCols;
                for (int c = 0; c < ecCols; c++) x[off + c] = _ec.Data[src + c];
                off += ecCols;
            }

            CopyRow(_er, regI, x, ref off);
            CopyRow(_et, typI, x, ref off);
            CopyRow(_eg, genI, x, ref off);

            if (_eo.Shape[0] > 0)
            {
                int idx = Math.Max(0, Math.Min(oriI, _eo.Shape[0] - 1));
                CopyRow(_eo, idx, x, ref off);
            }
            else
            {
                off += _dimOrigin;
            }

            // culture and parent projections are zero vectors in world/cascade calls
            off += CULT_PROJ;
            off += PAR_PROJ;

            var h1 = DenseTanh(x, _w1, _b1);
            var h2 = DenseTanh(h1, _w2, _b2);
            var logits = Dense(h2, _w3, _b3);
            return logits;
        }

        private static float[] DenseTanh(float[] x, Tensor w, Tensor b)
        {
            var y = Dense(x, w, b);
            for (int i = 0; i < y.Length; i++) y[i] = (float)Math.Tanh(y[i]);
            return y;
        }

        private static float[] Dense(float[] x, Tensor w, Tensor b)
        {
            int inDim = w.Shape[0];
            int outDim = w.Shape[1];
            var y = new float[outDim];

            for (int j = 0; j < outDim; j++)
            {
                double sum = b.Data[j];
                int wCol = j;
                for (int i = 0; i < inDim; i++)
                {
                    sum += x[i] * w.Data[i * outDim + wCol];
                }
                y[j] = (float)sum;
            }

            return y;
        }

        private static void CopyRow(Tensor t, int row, float[] dst, ref int dstOffset)
        {
            int cols = t.Shape[1];
            int r = Math.Max(0, Math.Min(row, t.Shape[0] - 1));
            int src = r * cols;
            Array.Copy(t.Data, src, dst, dstOffset, cols);
            dstOffset += cols;
        }

        private static int WeightedIndex(Rng64 rng, double[] weights)
        {
            if (weights == null || weights.Length == 0) return 0;
            double sum = 0;
            for (int i = 0; i < weights.Length; i++) sum += Math.Max(0, weights[i]);
            if (sum <= 0) return rng.NextInt(weights.Length);

            double roll = rng.NextDouble() * sum;
            double acc = 0;
            for (int i = 0; i < weights.Length; i++)
            {
                acc += Math.Max(0, weights[i]);
                if (roll <= acc) return i;
            }
            return weights.Length - 1;
        }

        private static double[] Normalize(double[] values)
        {
            var outv = new double[values.Length];
            double sum = 0;
            for (int i = 0; i < values.Length; i++)
            {
                outv[i] = Math.Max(0, values[i]);
                sum += outv[i];
            }

            if (sum <= 0)
            {
                for (int i = 0; i < outv.Length; i++) outv[i] = 1.0 / outv.Length;
                return outv;
            }

            for (int i = 0; i < outv.Length; i++) outv[i] /= sum;
            return outv;
        }

        private void ReadMetadata(Dictionary<string, object> meta)
        {
            string charsJson = GetMetaString(meta, "chars");
            string regionsJson = GetMetaString(meta, "regions");
            string regionWeightsJson = GetMetaString(meta, "region_weights");
            string genderPriorJson = GetMetaString(meta, "gender_prior");
            string regionRichnessJson = GetMetaString(meta, "region_richness", "[]");
            string originsJson = GetMetaString(meta, "origins", "[\"\"]");
            string dimsJson = GetMetaString(meta, "dims", "{}");

            _chars = ParseStringList(charsJson);
            Regions = ParseStringList(regionsJson);
            _regionWeights = ParseDoubleList(regionWeightsJson);
            _genderPrior = ParseDoubleList(genderPriorJson);
            _regionRichness = ParseIntList(regionRichnessJson);

            var origins = ParseStringList(originsJson);
            if (origins.Count == 0) origins.Add("");

            var dims = MiniJson.Deserialize(dimsJson) as Dictionary<string, object>;
            _k = ToInt(dims, "K", 4);
            _dimChar = ToInt(dims, "char", 24);
            _dimRegion = ToInt(dims, "region", 16);
            _dimType = ToInt(dims, "type", 16);
            _dimGender = ToInt(dims, "gender", 8);
            _dimOrigin = ToInt(dims, "origin", 12);
            _hidden = ToInt(dims, "hidden", 224);

            _charToIdx = new Dictionary<string, int>();
            for (int i = 0; i < _chars.Count; i++)
            {
                _charToIdx[_chars[i]] = CHAR_BASE + i;
            }
            _vocab = CHAR_BASE + _chars.Count;
        }

        private static string GetMetaString(Dictionary<string, object> meta, string key, string fallback = null)
        {
            if (!meta.TryGetValue(key, out var obj))
            {
                if (fallback != null) return fallback;
                throw new InvalidDataException("metadata key missing: " + key);
            }
            return Convert.ToString(obj, CultureInfo.InvariantCulture);
        }

        private static List<string> ParseStringList(string json)
        {
            var list = MiniJson.Deserialize(json) as List<object>;
            if (list == null) return new List<string>();
            var outList = new List<string>(list.Count);
            foreach (var x in list)
            {
                outList.Add(Convert.ToString(x, CultureInfo.InvariantCulture) ?? string.Empty);
            }
            return outList;
        }

        private static List<double> ParseDoubleList(string json)
        {
            var list = MiniJson.Deserialize(json) as List<object>;
            if (list == null) return new List<double>();
            var outList = new List<double>(list.Count);
            foreach (var x in list)
            {
                outList.Add(ToDouble(x));
            }
            return outList;
        }

        private static List<int> ParseIntList(string json)
        {
            var list = MiniJson.Deserialize(json) as List<object>;
            if (list == null) return new List<int>();
            var outList = new List<int>(list.Count);
            foreach (var x in list)
            {
                outList.Add((int)Math.Round(ToDouble(x)));
            }
            return outList;
        }

        private static int ToInt(Dictionary<string, object> d, string key, int fallback)
        {
            if (d == null || !d.TryGetValue(key, out var obj)) return fallback;
            return (int)Math.Round(ToDouble(obj));
        }

        private static double ToDouble(object x)
        {
            if (x is double dd) return dd;
            if (x is float ff) return ff;
            if (x is long ll) return ll;
            if (x is int ii) return ii;
            if (x is string ss && double.TryParse(ss, NumberStyles.Float, CultureInfo.InvariantCulture, out var d)) return d;
            return Convert.ToDouble(x, CultureInfo.InvariantCulture);
        }

        private static Tensor ReadTensor(Dictionary<string, object> header, byte[] raw, int dataBase, string name, bool optional = false)
        {
            if (!header.TryGetValue(name, out var infoObj))
            {
                if (optional) return null;
                throw new InvalidDataException("tensor missing: " + name);
            }

            var info = infoObj as Dictionary<string, object>;
            if (info == null)
            {
                throw new InvalidDataException("tensor header malformed: " + name);
            }

            if (!info.TryGetValue("dtype", out var dtypeObj) || Convert.ToString(dtypeObj, CultureInfo.InvariantCulture) != "F32")
            {
                throw new InvalidDataException("tensor dtype unsupported for " + name + " (expected F32)");
            }

            if (!info.TryGetValue("shape", out var shapeObj) || !(shapeObj is List<object> shapeList))
            {
                throw new InvalidDataException("tensor shape malformed: " + name);
            }

            var shape = new int[shapeList.Count];
            int count = 1;
            for (int i = 0; i < shapeList.Count; i++)
            {
                shape[i] = (int)Math.Round(ToDouble(shapeList[i]));
                count *= shape[i];
            }

            if (!info.TryGetValue("data_offsets", out var offsObj) || !(offsObj is List<object> offsList) || offsList.Count != 2)
            {
                throw new InvalidDataException("tensor data_offsets malformed: " + name);
            }

            int start = (int)Math.Round(ToDouble(offsList[0]));
            int end = (int)Math.Round(ToDouble(offsList[1]));
            int byteCount = end - start;
            if (byteCount != count * 4)
            {
                throw new InvalidDataException("tensor byte count mismatch: " + name);
            }

            int absStart = dataBase + start;
            if (absStart < 0 || absStart + byteCount > raw.Length)
            {
                throw new InvalidDataException("tensor out of bounds: " + name);
            }

            var data = new float[count];
            for (int i = 0; i < count; i++)
            {
                data[i] = BitConverter.ToSingle(raw, absStart + i * 4);
            }

            return new Tensor(shape, data);
        }

        private sealed class Tensor
        {
            public int[] Shape;
            public float[] Data;

            public Tensor(int[] shape, float[] data)
            {
                Shape = shape;
                Data = data;
            }

            public static Tensor Zeros(int[] shape)
            {
                int n = 1;
                for (int i = 0; i < shape.Length; i++) n *= shape[i];
                return new Tensor(shape, new float[n]);
            }
        }
    }

    // Minimal JSON parser sufficient for safetensors header and metadata.
    internal static class MiniJson
    {
        public static object Deserialize(string json)
        {
            if (json == null) return null;
            return Parser.Parse(json);
        }

        private sealed class Parser : IDisposable
        {
            private enum Token
            {
                None,
                CurlyOpen,
                CurlyClose,
                SquaredOpen,
                SquaredClose,
                Colon,
                Comma,
                String,
                Number,
                True,
                False,
                Null
            }

            private readonly string _json;
            private int _index;

            private Parser(string json)
            {
                _json = json;
                _index = 0;
            }

            public static object Parse(string json)
            {
                using (var parser = new Parser(json))
                {
                    return parser.ParseValue();
                }
            }

            public void Dispose() { }

            private Dictionary<string, object> ParseObject()
            {
                var table = new Dictionary<string, object>();
                EatChar();

                while (true)
                {
                    var token = NextToken;
                    if (token == Token.None) return null;
                    if (token == Token.Comma) continue;
                    if (token == Token.CurlyClose) return table;

                    var name = ParseString();
                    if (name == null) return null;
                    if (NextToken != Token.Colon) return null;
                    EatChar();
                    table[name] = ParseValue();
                }
            }

            private List<object> ParseArray()
            {
                var array = new List<object>();
                EatChar();

                bool parsing = true;
                while (parsing)
                {
                    Token token = NextToken;
                    switch (token)
                    {
                        case Token.None:
                            return null;
                        case Token.Comma:
                            continue;
                        case Token.SquaredClose:
                            parsing = false;
                            break;
                        default:
                            array.Add(ParseByToken(token));
                            break;
                    }
                }

                return array;
            }

            private object ParseValue()
            {
                Token token = NextToken;
                return ParseByToken(token);
            }

            private object ParseByToken(Token token)
            {
                switch (token)
                {
                    case Token.String:
                        return ParseString();
                    case Token.Number:
                        return ParseNumber();
                    case Token.CurlyOpen:
                        return ParseObject();
                    case Token.SquaredOpen:
                        return ParseArray();
                    case Token.True:
                        return true;
                    case Token.False:
                        return false;
                    case Token.Null:
                        return null;
                    default:
                        return null;
                }
            }

            private string ParseString()
            {
                var s = new StringBuilder();
                EatWhitespace();
                _index++;

                bool complete = false;
                while (!complete)
                {
                    if (_index == _json.Length) break;

                    char c = _json[_index++];
                    if (c == '"')
                    {
                        complete = true;
                        break;
                    }

                    if (c == '\\')
                    {
                        if (_index == _json.Length) break;
                        c = _json[_index++];
                        if (c == '"') s.Append('"');
                        else if (c == '\\') s.Append('\\');
                        else if (c == '/') s.Append('/');
                        else if (c == 'b') s.Append('\b');
                        else if (c == 'f') s.Append('\f');
                        else if (c == 'n') s.Append('\n');
                        else if (c == 'r') s.Append('\r');
                        else if (c == 't') s.Append('\t');
                        else if (c == 'u')
                        {
                            if (_index + 4 <= _json.Length)
                            {
                                string hex = _json.Substring(_index, 4);
                                if (uint.TryParse(hex, NumberStyles.HexNumber, CultureInfo.InvariantCulture, out uint codePoint))
                                {
                                    s.Append(char.ConvertFromUtf32((int)codePoint));
                                    _index += 4;
                                }
                            }
                        }
                    }
                    else
                    {
                        s.Append(c);
                    }
                }

                return s.ToString();
            }

            private object ParseNumber()
            {
                string number = NextWord;
                if (number.IndexOf('.') == -1 && number.IndexOf('e') == -1 && number.IndexOf('E') == -1)
                {
                    if (long.TryParse(number, NumberStyles.Integer, CultureInfo.InvariantCulture, out long parsedInt))
                    {
                        return parsedInt;
                    }
                }

                if (double.TryParse(number, NumberStyles.Float, CultureInfo.InvariantCulture, out double parsedDouble))
                {
                    return parsedDouble;
                }

                return 0.0;
            }

            private void EatWhitespace()
            {
                while (_index < _json.Length)
                {
                    char c = _json[_index];
                    if (c == ' ' || c == '\t' || c == '\n' || c == '\r') _index++;
                    else break;
                }
            }

            private char PeekChar => _index < _json.Length ? _json[_index] : '\0';
            private char NextChar => _index < _json.Length ? _json[_index++] : '\0';

            private string NextWord
            {
                get
                {
                    var sb = new StringBuilder();
                    while (_index < _json.Length && !IsWordBreak(_json[_index]))
                    {
                        sb.Append(_json[_index]);
                        _index++;
                    }
                    return sb.ToString();
                }
            }

            private Token NextToken
            {
                get
                {
                    EatWhitespace();
                    if (_index == _json.Length) return Token.None;

                    char c = PeekChar;
                    if (c == '{') return Token.CurlyOpen;
                    if (c == '}') { _index++; return Token.CurlyClose; }
                    if (c == '[') return Token.SquaredOpen;
                    if (c == ']') { _index++; return Token.SquaredClose; }
                    if (c == ',') { _index++; return Token.Comma; }
                    if (c == '"') return Token.String;
                    if (c == ':') return Token.Colon;
                    if (c == '-' || (c >= '0' && c <= '9')) return Token.Number;

                    string word = NextWord;
                    if (word == "false") return Token.False;
                    if (word == "true") return Token.True;
                    if (word == "null") return Token.Null;
                    return Token.None;
                }
            }

            /// <summary>Swallow one character. The NextToken PROPERTY above
            /// peeks without consuming for '{', '[', '"' and ':', so the
            /// parser has to eat those itself; this is that bite. Renamed from
            /// NextToken because C# cannot hold a property and a method of the
            /// same name, and the file would not compile at all (2026-08-08).</summary>
            private void EatChar()
            {
                var _ = NextChar;
            }

            private static bool IsWordBreak(char c)
            {
                return c == ' ' || c == '\t' || c == '\n' || c == '\r' || c == ',' || c == ':' || c == ']' || c == '}' || c == '[' || c == '{' || c == '"';
            }
        }
    }
}
