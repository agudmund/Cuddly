using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using UnityEngine;

namespace Wuddlies.Unity
{
    public enum WorldMix { Archive, Population, Equal }
    public enum NameType { Given, Surname }

    public static class WuddliesWorld
    {
        public const double DriftRateDefault = 0.12;
        public const double GenDriftRateDefault = 0.06;
        public const double WearEventsPerLineage = 0.75;

        private static readonly HashSet<string> FamilyFirstRegions = new HashSet<string>
        {
            "CN", "JP", "KR", "TW", "HK", "VN", "HU", "MN", "KH"
        };

        private static readonly Dictionary<string, NameProgram> RegionPrograms = new Dictionary<string, NameProgram>
        {
            {
                "IS",
                new NameProgram
                {
                    Id = "is_patronymic",
                    TokenSource = NameType.Given,
                    Order = NameOrder.GivenFirst,
                    ChildSuffix = new Dictionary<string, string>
                    {
                        { "M", "sson" },
                        { "F", "sdottir" },
                        { "U", "sson" }
                    },
                    TokenInherits = false
                }
            }
        };

        public static WorldCensus PourWorld(INameSource model, WorldOptions options)
        {
            int actualSeed = options.Seed ?? unchecked((int)(DateTime.UtcNow.Ticks & 0x7FFFFFFF));
            int childrenMax = options.ChildrenMax ?? Math.Max(1, options.Souls - 1);
            double wearRate = options.WearRate ?? DefaultWear(options.Generations);

            var root = new SeedCascade(actualSeed);
            var settlements = root.Spawn(options.Settlements);

            var outCensus = new WorldCensus
            {
                Seed = actualSeed,
                World = options.World,
                Generations = options.Generations,
                Settlements = new List<SettlementCensus>()
            };

            for (int i = 0; i < settlements.Count; i++)
            {
                bool isConfluence = i >= options.Settlements - options.Confluences;
                var split = new SeedCascade(settlements[i]).Spawn(3);
                var foundingRng = new Rng64(split[0]);
                var driftRng = new Rng64(split[1]);
                ulong familySeed = split[2];

                string DrawRegion(Rng64 rng)
                {
                    if (!string.IsNullOrWhiteSpace(options.Region))
                    {
                        return options.Region.ToUpperInvariant();
                    }

                    var weights = model.RegionDrawWeights(options.World);
                    return model.Regions[rng.WeightedIndex(weights)];
                }

                NameProgram program;
                List<string> driftLog = new List<string>();
                string mintSoil;
                string[] roots = null;
                string eponym;

                if (isConfluence)
                {
                    string rootA;
                    string rootB;
                    if (options.Roots != null && options.Roots.Length == 2)
                    {
                        rootA = options.Roots[0].ToUpperInvariant();
                        rootB = options.Roots[1].ToUpperInvariant();
                    }
                    else
                    {
                        rootA = DrawRegion(foundingRng);
                        rootB = DrawRegion(foundingRng);
                    }

                    eponym = model.SampleName(foundingRng, rootA, NameType.Surname, null, options.Temperature)
                             + "-"
                             + model.SampleName(foundingRng, rootB, NameType.Surname, null, options.Temperature);
                    var cross = Crossover(BaseProgramFor(rootA), BaseProgramFor(rootB), rootA, rootB, driftRng);
                    program = cross.Program;
                    driftLog.AddRange(cross.Log);
                    mintSoil = rootA;
                    roots = new[] { rootA, rootB };
                }
                else
                {
                    string region = DrawRegion(foundingRng);
                    eponym = model.SampleName(foundingRng, region, NameType.Surname, null, options.Temperature);
                    var drifted = MaybeDrift(BaseProgramFor(region), driftRng, options.DriftRate, "founding drift");
                    program = drifted.Program;
                    driftLog.AddRange(drifted.Log);
                    mintSoil = region;
                }

                var programs = new List<NameProgram> { program.Clone() };
                for (int g = 1; g <= options.Generations; g++)
                {
                    var next = MaybeDrift(programs[programs.Count - 1], driftRng, options.GenDriftRate, "generation " + g + " drift");
                    programs.Add(next.Program);
                    driftLog.AddRange(next.Log);
                }

                var familyRoots = new List<string>();
                if (isConfluence)
                {
                    for (int f = 0; f < options.Families; f++)
                    {
                        familyRoots.Add(driftRng.NextDouble() < 0.5 ? roots[0] : roots[1]);
                    }
                }
                else
                {
                    for (int f = 0; f < options.Families; f++)
                    {
                        familyRoots.Add(mintSoil);
                    }
                }

                var pinnedRoots = new List<string>();
                if (!string.IsNullOrWhiteSpace(options.RootName))
                {
                    pinnedRoots.Add(options.RootName);
                    for (int f = 1; f < options.Families; f++)
                    {
                        pinnedRoots.Add(null);
                    }
                }

                var families = PourHistory(
                    model,
                    familySeed,
                    familyRoots,
                    programs,
                    options.Generations,
                    childrenMax,
                    driftLog,
                    options.PromotionsOn,
                    options.Temperature,
                    pinnedRoots.Count == 0 ? null : pinnedRoots,
                    wearRate,
                    driftRng);

                outCensus.Settlements.Add(new SettlementCensus
                {
                    Region = mintSoil,
                    Roots = roots,
                    Eponym = eponym,
                    Programs = programs,
                    Drift = driftLog,
                    Families = families
                });
            }

            return outCensus;
        }

        public static string PrintWorld(WorldCensus census)
        {
            var sb = new StringBuilder();
            sb.AppendLine("[world] seed " + census.Seed + ", " + census.World.ToString().ToLowerInvariant() + " mix, "
                          + census.Generations + " generation(s): " + census.Settlements.Count + " settlements");

            foreach (var s in census.Settlements)
            {
                if (s.Roots != null && s.Roots.Length == 2)
                {
                    sb.AppendLine();
                    sb.AppendLine("  ~ the " + s.Eponym + " confluence (" + s.Roots[0] + " x " + s.Roots[1] + ") ~");
                }
                else
                {
                    sb.AppendLine();
                    sb.AppendLine("  ~ the " + s.Eponym + " settlement (" + s.Region + ") ~");
                }

                foreach (var line in s.Drift)
                {
                    sb.AppendLine("    * " + line);
                }

                foreach (var fam in s.Families)
                {
                    bool tokenInherits = s.Programs != null && s.Programs.Count > 0 && s.Programs[0].TokenInherits;
                    string label = tokenInherits ? "house of" : "line of";
                    string tag = (s.Roots != null && s.Roots.Length == 2) ? " (" + fam.Region + ")" : string.Empty;
                    string lawTag = !string.IsNullOrWhiteSpace(fam.LawEcho) ? "  [the name " + fam.LawEcho + " carries]" : string.Empty;
                    sb.AppendLine("    " + label + " " + fam.Token + tag + ":" + lawTag);
                    for (int i = 0; i < fam.Souls.Count; i++)
                    {
                        PrintSoul(fam.Souls[i], "    ", i == fam.Souls.Count - 1, sb);
                    }
                }
            }

            return sb.ToString();
        }

        public static double DefaultWear(int generations)
        {
            return WearEventsPerLineage / Math.Max(generations, 1);
        }

        private static void PrintSoul(Soul soul, string prefix, bool last, StringBuilder sb)
        {
            string branch = last ? "`- " : "|- ";
            sb.AppendLine(prefix + branch + soul.Name + "  (" + soul.Gender + ")");
            string ext = last ? "   " : "|  ";
            for (int i = 0; i < soul.Children.Count; i++)
            {
                PrintSoul(soul.Children[i], prefix + ext, i == soul.Children.Count - 1, sb);
            }
        }

        private static NameProgram BaseProgramFor(string region)
        {
            if (RegionPrograms.TryGetValue(region, out var program))
            {
                return program.Clone();
            }

            return new NameProgram
            {
                Id = "inherited_surname",
                TokenSource = NameType.Surname,
                Order = FamilyFirstRegions.Contains(region) ? NameOrder.FamilyFirst : NameOrder.GivenFirst,
                ChildSuffix = null,
                TokenInherits = true
            };
        }

        private static string Assemble(NameProgram program, string token, string given, string gender)
        {
            string worn = token;
            if (program.ChildSuffix != null)
            {
                if (!program.ChildSuffix.TryGetValue(gender, out var suffix)) suffix = "";
                worn = token + suffix;
            }

            return program.Order == NameOrder.FamilyFirst ? (worn + " " + given) : (given + " " + worn);
        }

        private static (NameProgram Program, List<string> Log) MaybeDrift(NameProgram program, Rng64 rng, double driftRate, string stamp)
        {
            if (driftRate <= 0 || rng.NextDouble() >= driftRate)
            {
                return (program.Clone(), new List<string>());
            }

            var prog = program.Clone();
            var log = new List<string>();

            string[] kinds = { "suffix", "suffix", "suffix", "order", "source" };
            string kind = kinds[rng.NextInt(kinds.Length)];

            if (kind == "suffix" && prog.ChildSuffix != null)
            {
                var suffixes = new Dictionary<string, string>(prog.ChildSuffix);
                string[] gs = { "M", "F", "U" };
                string g = gs[rng.NextInt(gs.Length)];
                string old = suffixes.ContainsKey(g) ? suffixes[g] : "";
                string nw = WeatherSuffix(old, rng);
                if (nw != old)
                {
                    suffixes[g] = nw;
                    prog.ChildSuffix = suffixes;
                    prog.Id = prog.Id + "+worn";
                    log.Add(stamp + ": the " + g + " particle weathered " + old + " -> " + nw);
                }
            }
            else if (kind == "order")
            {
                prog.Order = prog.Order == NameOrder.GivenFirst ? NameOrder.FamilyFirst : NameOrder.GivenFirst;
                prog.Id = prog.Id + "+flipped";
                log.Add(stamp + ": name order flipped to " + (prog.Order == NameOrder.FamilyFirst ? "family_first" : "given_first"));
            }
            else
            {
                if (prog.TokenSource == NameType.Surname)
                {
                    prog.TokenSource = NameType.Given;
                    prog.ChildSuffix = new Dictionary<string, string>
                    {
                        { "M", "sson" },
                        { "F", "sdottir" },
                        { "U", "sson" }
                    };
                    prog.TokenInherits = false;
                    prog.Id = "went_patronymic";
                    log.Add(stamp + ": this settlement went patronymic (a parent's name now carries)");
                }
                else
                {
                    prog.TokenSource = NameType.Surname;
                    prog.ChildSuffix = null;
                    prog.TokenInherits = true;
                    prog.Id = "settled_surnames";
                    log.Add(stamp + ": patronymics froze into standing surnames");
                }
            }

            return (prog, log);
        }

        private static (NameProgram Program, List<string> Log) Crossover(NameProgram a, NameProgram b, string rootA, string rootB, Rng64 rng)
        {
            bool srcA = rng.NextInt(2) == 1;
            bool ordA = rng.NextInt(2) == 1;
            var srcParent = srcA ? a : b;
            var ordParent = ordA ? a : b;
            string srcRoot = srcA ? rootA : rootB;
            string ordRoot = ordA ? rootA : rootB;

            var prog = new NameProgram
            {
                Id = "confluence(" + rootA + "x" + rootB + ")",
                TokenSource = srcParent.TokenSource,
                TokenInherits = srcParent.TokenInherits,
                Order = ordParent.Order,
                ChildSuffix = null
            };

            var log = new List<string>
            {
                "confluence: the token walks " + srcRoot + "'s way (" + prog.TokenSource.ToString().ToLowerInvariant() + "); name order follows " + ordRoot + " (" + (prog.Order == NameOrder.FamilyFirst ? "family_first" : "given_first") + ")"
            };

            if (a.ChildSuffix != null && b.ChildSuffix != null)
            {
                prog.ChildSuffix = new Dictionary<string, string>();
                foreach (var g in new[] { "M", "F", "U" })
                {
                    prog.ChildSuffix[g] = (rng.NextInt(2) == 1 ? a.ChildSuffix[g] : b.ChildSuffix[g]);
                }
                log.Add("confluence: the particles blended from both herds");
            }
            else if ((a.ChildSuffix != null || b.ChildSuffix != null) && prog.TokenSource == NameType.Given)
            {
                prog.ChildSuffix = new Dictionary<string, string>(a.ChildSuffix ?? b.ChildSuffix);
                log.Add("confluence: the particles arrived with one herd");
            }

            return (prog, log);
        }

        private static List<FamilyLine> PourHistory(
            INameSource model,
            ulong seed,
            List<string> familyRoots,
            List<NameProgram> programs,
            int generations,
            int childrenMax,
            List<string> driftLog,
            bool promotionsOn,
            double temperature,
            List<string> rootNames,
            double wearRate,
            Rng64 watcherRng)
        {
            var famSeeds = new SeedCascade(seed).Spawn(familyRoots.Count);
            var families = new List<FamilyLine>();

            for (int i = 0; i < familyRoots.Count; i++)
            {
                var frng = new Rng64(famSeeds[i]);
                string token = !string.IsNullOrWhiteSpace(rootNames != null && i < rootNames.Count ? rootNames[i] : null)
                    ? rootNames[i]
                    : model.SampleName(frng, familyRoots[i], programs[0].TokenSource, null, temperature);

                families.Add(new FamilyLine
                {
                    Token = token,
                    Region = familyRoots[i],
                    Souls = new List<Soul>(),
                    LawEcho = null,
                    PendingNodes = new List<SoulNode>
                    {
                        new SoulNode { Parent = null, Seed = frng.NextULong() }
                    }
                });
            }

            for (int gen = 1; gen <= generations; gen++)
            {
                var level = new List<(Soul Soul, FamilyLine Family)>();
                var nextFrontier = new Dictionary<FamilyLine, List<SoulNode>>();
                var program = programs[Math.Min(gen, programs.Count - 1)];

                foreach (var fam in families)
                {
                    if (!nextFrontier.ContainsKey(fam)) nextFrontier[fam] = new List<SoulNode>();

                    foreach (var node in fam.PendingNodes)
                    {
                        var parent = node.Parent;
                        var rng = new Rng64(node.Seed);
                        int nKids = rng.NextInt(childrenMax) + 1;

                        for (int k = 0; k < nKids; k++)
                        {
                            var kidRng = new Rng64(rng.NextULong());
                            string gender = model.SampleGender(kidRng);
                            string given = model.SampleName(kidRng, fam.Region, NameType.Given, gender, temperature);

                            string token;
                            if (program.TokenInherits)
                            {
                                string carried = (parent != null && !string.IsNullOrWhiteSpace(parent.Token)) ? parent.Token : fam.Token;
                                if (wearRate > 0 && kidRng.NextDouble() < wearRate)
                                {
                                    string worn = WearToken(carried, kidRng);
                                    if (worn != carried)
                                    {
                                        driftLog.Add("generation " + gen + ": the " + carried + " name wore to " + worn + " in " + given + "'s line");
                                        carried = worn;
                                    }
                                }
                                token = carried;
                            }
                            else
                            {
                                token = parent != null ? parent.Given : fam.Token;
                            }

                            var soul = new Soul
                            {
                                Given = given,
                                Gender = gender,
                                Gen = gen,
                                Token = token,
                                ParentGiven = parent != null ? parent.Given : null,
                                Name = Assemble(program, token, given, gender),
                                Children = new List<Soul>()
                            };

                            if (parent == null) fam.Souls.Add(soul);
                            else parent.Children.Add(soul);

                            level.Add((soul, fam));
                            nextFrontier[fam].Add(new SoulNode { Parent = soul, Seed = kidRng.NextULong() });
                        }
                    }
                }

                if (promotionsOn && gen < generations)
                {
                    var promoted = WatchTraditions(gen, level, programs[Math.Min(gen + 1, programs.Count - 1)], watcherRng);
                    for (int j = gen + 1; j < programs.Count; j++)
                    {
                        programs[j] = promoted;
                    }
                }

                foreach (var fam in families)
                {
                    fam.PendingNodes = nextFrontier[fam];
                }
            }

            foreach (var fam in families)
            {
                fam.PendingNodes = null;
            }

            return families;
        }

        private static NameProgram WatchTraditions(int gen, List<(Soul Soul, FamilyLine Family)> level, NameProgram program, Rng64 rng)
        {
            var prog = program.Clone();
            if (level.Count < 4) return prog;

            var counts = new Dictionary<char, int>();
            foreach (var row in level)
            {
                if (string.IsNullOrWhiteSpace(row.Soul.Given)) continue;
                char c = char.ToUpperInvariant(row.Soul.Given[0]);
                counts[c] = counts.TryGetValue(c, out var n) ? n + 1 : 1;
            }

            if (counts.Count == 0) return prog;
            var top = counts.OrderByDescending(kv => kv.Value).First();
            if ((double)top.Value / level.Count >= 0.5)
            {
                prog.Initial = top.Key.ToString();
                prog.InitialBorn = gen + 1;
                prog.Id = prog.Id + "+initial(" + prog.Initial + ")";
            }

            return prog;
        }

        private static string WeatherSuffix(string suffix, Rng64 rng)
        {
            if (string.IsNullOrEmpty(suffix)) return suffix;
            var options = new List<string>();
            string vowels = "aeiouy";

            for (int i = 0; i < suffix.Length - 1; i++)
            {
                if (suffix[i] == suffix[i + 1])
                {
                    options.Add(suffix.Remove(i, 1));
                }
            }

            var vowelPositions = suffix.Select((ch, idx) => (ch, idx)).Where(x => vowels.IndexOf(char.ToLowerInvariant(x.ch)) >= 0).Select(x => x.idx).ToList();
            if (vowelPositions.Count > 0)
            {
                int i = vowelPositions[rng.NextInt(vowelPositions.Count)];
                char repl = vowels[rng.NextInt(vowels.Length)];
                var chars = suffix.ToCharArray();
                chars[i] = repl;
                options.Add(new string(chars));
            }

            return options.Count == 0 ? suffix : options[rng.NextInt(options.Count)];
        }

        private static string WearToken(string token, Rng64 rng)
        {
            if (string.IsNullOrWhiteSpace(token)) return token;
            var options = new List<string>();
            string vowels = "aeiouy";

            for (int i = 0; i < token.Length - 1; i++)
            {
                if (char.ToLowerInvariant(token[i]) == char.ToLowerInvariant(token[i + 1]))
                {
                    options.Add(token.Remove(i, 1));
                }
            }

            var vowelPositions = token.Select((ch, idx) => (ch, idx)).Where(x => vowels.IndexOf(char.ToLowerInvariant(x.ch)) >= 0).Select(x => x.idx).ToList();
            if (vowelPositions.Count > 0)
            {
                int i = vowelPositions[rng.NextInt(vowelPositions.Count)];
                char old = char.ToLowerInvariant(token[i]);
                var choices = vowels.Where(v => v != old).ToArray();
                char repl = choices[rng.NextInt(choices.Length)];
                var chars = token.ToCharArray();
                chars[i] = repl;
                options.Add(new string(chars));
            }

            if (token.Length > 6)
            {
                options.Add(token.Substring(0, token.Length - 1));
            }

            return options.Count == 0 ? token : options[rng.NextInt(options.Count)];
        }
    }

    public interface INameSource
    {
        List<string> Regions { get; }
        double[] RegionDrawWeights(WorldMix world);
        string SampleName(Rng64 rng, string region, NameType type, string gender, double temperature);
        string SampleGender(Rng64 rng);
    }

    public class SimpleNameSource : INameSource
    {
        public List<string> Regions { get; } = new List<string> { "GB", "IN", "JP", "IS", "GH", "BR", "US", "TR" };

        private readonly Dictionary<string, string[]> _givenSyllables = new Dictionary<string, string[]>
        {
            { "GB", new[] { "al", "be", "cor", "dan", "el", "fin", "gra", "har", "ivy", "jo" } },
            { "IN", new[] { "aan", "di", "kar", "lee", "na", "raj", "shi", "tan", "vi", "ya" } },
            { "JP", new[] { "a", "ki", "na", "ri", "ta", "yo", "mi", "sa", "ko", "to" } },
            { "IS", new[] { "arn", "bjorn", "eir", "finn", "gud", "hal", "ing", "kat", "run", "sve" } },
            { "GH", new[] { "ama", "ko", "kw", "na", "ofi", "yaa", "ad", "jo", "esi", "taa" } },
            { "BR", new[] { "ana", "be", "ca", "do", "ela", "fer", "gui", "leo", "mar", "ro" } },
            { "US", new[] { "ash", "blake", "cam", "drew", "elli", "flyn", "gray", "hay", "ivy", "jules" } },
            { "TR", new[] { "ay", "bar", "cem", "den", "el", "fer", "gul", "han", "il", "jas" } }
        };

        private readonly Dictionary<string, string[]> _surnameSyllables = new Dictionary<string, string[]>
        {
            { "GB", new[] { "ash", "brook", "clark", "dale", "ford", "green", "hart", "stone" } },
            { "IN", new[] { "dev", "kar", "lal", "man", "pat", "rao", "sen", "var" } },
            { "JP", new[] { "aoi", "kawa", "mori", "naka", "sato", "taka", "yama", "zaki" } },
            { "IS", new[] { "arn", "eirik", "gud", "hall", "jon", "sig", "thor", "val" } },
            { "GH", new[] { "adu", "boat", "kofi", "mens", "nkr", "owu", "quar", "yaw" } },
            { "BR", new[] { "costa", "dias", "fer", "gomes", "lima", "mora", "sil", "souza" } },
            { "US", new[] { "baker", "carter", "davis", "mason", "parker", "reed", "taylor", "walker" } },
            { "TR", new[] { "ars", "demir", "kaya", "oz", "sari", "tan", "yil", "zen" } }
        };

        public double[] RegionDrawWeights(WorldMix world)
        {
            switch (world)
            {
                case WorldMix.Equal:
                    return Enumerable.Repeat(1.0, Regions.Count).ToArray();
                case WorldMix.Population:
                    return new[] { 0.10, 0.20, 0.12, 0.04, 0.10, 0.14, 0.20, 0.10 };
                default:
                    return new[] { 0.16, 0.14, 0.13, 0.10, 0.09, 0.12, 0.14, 0.12 };
            }
        }

        public string SampleGender(Rng64 rng)
        {
            double roll = rng.NextDouble();
            if (roll < 0.49) return "M";
            if (roll < 0.98) return "F";
            return "U";
        }

        public string SampleName(Rng64 rng, string region, NameType type, string gender, double temperature)
        {
            if (!Regions.Contains(region))
            {
                region = Regions[rng.NextInt(Regions.Count)];
            }

            var pool = type == NameType.Given ? _givenSyllables[region] : _surnameSyllables[region];
            int parts = type == NameType.Given ? (rng.NextDouble() < 0.7 ? 2 : 3) : 2;
            var sb = new StringBuilder();
            for (int i = 0; i < parts; i++)
            {
                sb.Append(pool[rng.NextInt(pool.Length)]);
            }

            string raw = sb.ToString();
            if (string.IsNullOrWhiteSpace(raw)) raw = "nameless";
            return char.ToUpperInvariant(raw[0]) + raw.Substring(1);
        }
    }

    public class WorldOptions
    {
        public int? Seed = null;
        public int Settlements = 3;
        public int Families = 3;
        public int Souls = 4;
        public WorldMix World = WorldMix.Population;
        public string Region = null;
        public double DriftRate = WuddliesWorld.DriftRateDefault;
        public int Generations = 1;
        public int? ChildrenMax = null;
        public double GenDriftRate = WuddliesWorld.GenDriftRateDefault;
        public int Confluences = 0;
        public string[] Roots = null;
        public bool PromotionsOn = true;
        public double Temperature = 0.9;
        public string RootName = null;
        public double? WearRate = null;
    }

    public enum NameOrder { GivenFirst, FamilyFirst }

    public class NameProgram
    {
        public string Id;
        public NameType TokenSource;
        public NameOrder Order;
        public Dictionary<string, string> ChildSuffix;
        public bool TokenInherits;
        public string Initial;
        public int? InitialBorn;

        public NameProgram Clone()
        {
            return new NameProgram
            {
                Id = Id,
                TokenSource = TokenSource,
                Order = Order,
                ChildSuffix = ChildSuffix == null ? null : new Dictionary<string, string>(ChildSuffix),
                TokenInherits = TokenInherits,
                Initial = Initial,
                InitialBorn = InitialBorn
            };
        }
    }

    public class WorldCensus
    {
        public int Seed;
        public WorldMix World;
        public int Generations;
        public List<SettlementCensus> Settlements;
    }

    public class SettlementCensus
    {
        public string Region;
        public string[] Roots;
        public string Eponym;
        public List<NameProgram> Programs;
        public List<string> Drift;
        public List<FamilyLine> Families;
    }

    public class FamilyLine
    {
        public string Token;
        public string Region;
        public List<Soul> Souls;
        public string LawEcho;
        public List<SoulNode> PendingNodes;
    }

    public class Soul
    {
        public string Given;
        public string Gender;
        public int Gen;
        public string Token;
        public string ParentGiven;
        public string Name;
        public List<Soul> Children;
    }

    public class SoulNode
    {
        public Soul Parent;
        public ulong Seed;
    }

    public class SeedCascade
    {
        private readonly ulong _entropy;
        private readonly ulong _spawnPath;
        private ulong _spawnCounter;

        public SeedCascade(int seed)
        {
            _entropy = Mix((ulong)(uint)seed ^ 0x8F7A56E319CA53D1UL);
            _spawnPath = 0UL;
            _spawnCounter = 0UL;
        }

        public SeedCascade(ulong seed)
        {
            _entropy = Mix(seed ^ 0x8F7A56E319CA53D1UL);
            _spawnPath = 0UL;
            _spawnCounter = 0UL;
        }

        private SeedCascade(ulong entropy, ulong spawnPath, ulong spawnCounter)
        {
            _entropy = entropy;
            _spawnPath = spawnPath;
            _spawnCounter = spawnCounter;
        }

        public SeedCascade SpawnOne()
        {
            ulong id = _spawnCounter++;
            ulong childPath = Mix(_spawnPath ^ id ^ 0x9E3779B97F4A7C15UL);
            return new SeedCascade(_entropy, childPath, 0UL);
        }

        public ulong NextSeed()
        {
            ulong lane = _spawnCounter++;
            return Mix(_entropy ^ RotateLeft(_spawnPath, 17) ^ lane ^ 0xD2B74407B1CE6E93UL);
        }

        public List<ulong> Spawn(int count)
        {
            var outSeeds = new List<ulong>(count);
            for (int i = 0; i < count; i++)
            {
                outSeeds.Add(NextSeed());
            }
            return outSeeds;
        }

        private static ulong RotateLeft(ulong value, int bits)
        {
            bits &= 63;
            return (value << bits) | (value >> (64 - bits));
        }

        private static ulong Mix(ulong x)
        {
            x += 0x9E3779B97F4A7C15UL;
            x = (x ^ (x >> 30)) * 0xBF58476D1CE4E5B9UL;
            x = (x ^ (x >> 27)) * 0x94D049BB133111EBUL;
            return x ^ (x >> 31);
        }
    }

    public class Rng64
    {
        private ulong _state;
        private ulong _inc;

        public Rng64(ulong seed)
        {
            // PCG-style seeding: two mixed lanes make state and stream selector.
            _state = 0UL;
            _inc = (Mix(seed ^ 0xDA3E39CB94B95BDBUL) << 1) | 1UL;
            NextUInt32();
            _state += Mix(seed ^ 0xA4093822299F31D0UL);
            NextUInt32();
        }

        public ulong NextULong()
        {
            ulong hi = NextUInt32();
            ulong lo = NextUInt32();
            return (hi << 32) | lo;
        }

        public int NextInt(int maxExclusive)
        {
            if (maxExclusive <= 1) return 0;
            return (int)(NextULong() % (ulong)maxExclusive);
        }

        public double NextDouble()
        {
            return (NextULong() >> 11) * (1.0 / (1UL << 53));
        }

        private uint NextUInt32()
        {
            ulong oldState = _state;
            _state = unchecked(oldState * 6364136223846793005UL + _inc);
            uint xorshifted = (uint)(((oldState >> 18) ^ oldState) >> 27);
            int rot = (int)(oldState >> 59);
            return (xorshifted >> rot) | (xorshifted << ((-rot) & 31));
        }

        private static ulong Mix(ulong x)
        {
            x += 0x9E3779B97F4A7C15UL;
            x = (x ^ (x >> 30)) * 0xBF58476D1CE4E5B9UL;
            x = (x ^ (x >> 27)) * 0x94D049BB133111EBUL;
            return x ^ (x >> 31);
        }

        public int WeightedIndex(double[] weights)
        {
            if (weights == null || weights.Length == 0)
            {
                return 0;
            }

            double sum = 0;
            for (int i = 0; i < weights.Length; i++)
            {
                sum += Math.Max(0, weights[i]);
            }

            if (sum <= 0) return NextInt(weights.Length);

            double roll = NextDouble() * sum;
            double acc = 0;
            for (int i = 0; i < weights.Length; i++)
            {
                acc += Math.Max(0, weights[i]);
                if (roll <= acc) return i;
            }

            return weights.Length - 1;
        }
    }
}
