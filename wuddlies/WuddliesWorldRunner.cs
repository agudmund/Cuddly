using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using UnityEngine;

namespace Wuddlies.Unity
{
    public class WuddliesWorldRunner : MonoBehaviour
    {
        [Header("Seed is optional; enable to lock determinism")]
        public bool UseSeed = true;
        public int Seed = 3124;
        public int Settlements = 3;
        public int Families = 3;
        public int Souls = 4;
        public int Generations = 1;
        public bool PromotionsOn = true;

        [Header("Optional real weight (.safetensors)")]
        public TextAsset WeightAsset;
        public string WeightPath;
        public bool FallbackToSimpleSource = true;

        [TextArea(10, 40)]
        public string LastWorld;

        [ContextMenu("Generate World")]
        public void GenerateWorld()
        {
            INameSource model = BuildNameSource();
            var options = new WorldOptions
            {
                Seed = UseSeed ? Seed : (int?)null,
                Settlements = Settlements,
                Families = Families,
                Souls = Souls,
                World = WorldMix.Population,
                Region = null,
                DriftRate = WuddliesWorld.DriftRateDefault,
                GenDriftRate = WuddliesWorld.GenDriftRateDefault,
                Confluences = 0,
                Roots = null,
                PromotionsOn = PromotionsOn,
                Temperature = 0.9,
                RootName = null,
                WearRate = null,
                Generations = Generations,
                ChildrenMax = null
            };

            var census = WuddliesWorld.PourWorld(model, options);
            LastWorld = WuddliesWorld.PrintWorld(census);
            Debug.Log(LastWorld);
        }

        private void Start()
        {
            GenerateWorld();
        }

        private INameSource BuildNameSource()
        {
            try
            {
                if (WeightAsset != null && WeightAsset.bytes != null && WeightAsset.bytes.Length > 0)
                {
                    return WuddliesSafetensorsNameSource.LoadFromBytes(WeightAsset.bytes);
                }

                if (!string.IsNullOrWhiteSpace(WeightPath))
                {
                    string path = WeightPath;
                    if (!Path.IsPathRooted(path))
                    {
                        path = Path.GetFullPath(Path.Combine(Application.dataPath, "..", path));
                    }
                    return WuddliesSafetensorsNameSource.LoadFromFile(path);
                }
            }
            catch (Exception ex)
            {
                Debug.LogWarning("[wuddlies] failed to load safetensors model: " + ex.Message);
                if (!FallbackToSimpleSource)
                {
                    throw;
                }
            }

            return new SimpleNameSource();
        }
    }
}
