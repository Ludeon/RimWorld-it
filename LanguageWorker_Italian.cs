// LanguageWorker_Italian — improved article and plural handling.
// Updated: 2026-06-12
//
// ============================================================================
// STRATEGY NOTE — this file is NOT shipped and NOT loaded by the translation.
// ============================================================================
// The Italian translation is a pure language pack (XML/TXT only). The game
// resolves <languageWorkerClass>LanguageWorker_Italian</languageWorkerClass>
// by name to the engine's BUILT-IN class, so this .cs is never compiled or run
// by a data-only pack. We therefore drive grammar entirely through DATA + RULES,
// the same way the German pack does (no custom worker at all):
//   - WordInfo/plural.txt  -> noun plurals (lookup wins over the engine algorithm;
//                             fixes "figlii"->"figli", "amica"->"amiche", and the
//                             heteroclite forms such as braccio->braccia).
//   - WordInfo/Gender/*    -> ResolveGender for engine-inserted articles.
//   - rulesStrings         -> we write the correct article inline (e.g. "le braccia",
//                             "gli animali"), instead of relying on the engine.
// The engine pluralizes first and resolves gender on the already-pluralized string
// (verified: WithDefiniteArticle(Pluralize(label), ResolveGender(Pluralize(label)),
// plural:true)), so plural.txt + Gender already yield the right gender. The one
// thing the stock worker cannot do is FORM the plural article (i/gli/le, dei/degli/
// delle) — that is the only residual the data path leaves slightly imperfect for
// text the engine auto-assembles. We accept that residual.
//
// This file is kept ONLY as a candidate for an upstream PR to Ludeon (to fix the
// stock Italian worker for all users). It is not a prerequisite for the pack.
//
// Changes over the previous version:
//   1. Definite article "lo" now also applies to words starting with gn, ps, pn,
//      x, y, and i+vowel (lo gnomo, lo psicologo, lo pneumatico, lo xilofono,
//      lo yogurt, lo iato). Previously these produced "il psicologo" / "il gnomo".
//   2. Mute "h" before a vowel is treated as a vowel sound for elision, so foreign
//      words elide correctly (l'hotel, un'hostess, gli hotel).
//   3. Plural articles are now handled (previously they fell through to the
//      singular forms): i/gli/le and the partitives dei/degli/delle.
//   4. Plurals:
//      - words ending in -io collapse to a single -i (figlio -> figli,
//        occhio -> occhi, studio -> studi); the previous code produced "figlii".
//      - masculine -ca/-ga -> -chi/-ghi (duca -> duchi, collega -> colleghi);
//        feminine -ca/-ga -> -che/-ghe (amica -> amiche, collega -> colleghe).
//      - feminine -cia/-gia -> -cie/-gie or -ce/-ge depending on the preceding
//        letter (camicia -> camicie, faccia -> facce).
//      Irregular plurals remain handled by TryLookupPluralForm and the WordInfo
//      gender data.

using Verse;

namespace Verse
{
    public class LanguageWorker_Italian : LanguageWorker
    {
        private const string Vowels = "aeiouAEIOU";

        public bool IsVowel(char ch)
        {
            return Vowels.IndexOf(ch) >= 0;
        }

        // True if the word begins with a vowel sound for elision purposes:
        // an actual vowel, or a mute "h" followed by a vowel (hotel, hostess).
        private bool StartsWithVowelSound(string str)
        {
            char c = str[0];
            if (IsVowel(c))
                return true;
            if ((c == 'h' || c == 'H') && str.Length >= 2 && IsVowel(str[1]))
                return true;
            return false;
        }

        // True if a masculine word requires "lo / uno / gli / degli":
        // impure s (s + consonant), z, x, y, ps, pn, gn, i + vowel (semivowel).
        private bool MasculineNeedsLo(string str)
        {
            char c0 = char.ToLower(str[0]);
            char c1 = (str.Length >= 2) ? char.ToLower(str[1]) : '\0';
            bool secondIsVowel = (str.Length >= 2) && IsVowel(str[1]);

            if (c0 == 'z' || c0 == 'x' || c0 == 'y')
                return true;
            if (c0 == 's' && !secondIsVowel)        // impure s
                return true;
            if (c0 == 'p' && (c1 == 's' || c1 == 'n'))  // ps, pn
                return true;
            if (c0 == 'g' && c1 == 'n')              // gn
                return true;
            if (c0 == 'i' && secondIsVowel)          // i + vowel: lo iato, lo ione
                return true;
            return false;
        }

        public override string WithIndefiniteArticle(string str, Gender gender, bool plural = false, bool name = false)
        {
            if (str.NullOrEmpty() || name)
                return str;

            if (plural)   // partitive: dei / degli / delle
            {
                if (gender == Gender.Female)
                    return "delle " + str;
                return ((MasculineNeedsLo(str) || StartsWithVowelSound(str)) ? "degli " : "dei ") + str;
            }

            if (gender == Gender.Female)
                return (StartsWithVowelSound(str) ? "un'" : "una ") + str;
            if (MasculineNeedsLo(str))
                return "uno " + str;
            return "un " + str;
        }

        public override string WithDefiniteArticle(string str, Gender gender, bool plural = false, bool name = false)
        {
            if (str.NullOrEmpty() || name)
                return str;

            if (plural)   // i / gli / le
            {
                if (gender == Gender.Female)
                    return "le " + str;
                return ((MasculineNeedsLo(str) || StartsWithVowelSound(str)) ? "gli " : "i ") + str;
            }

            if (gender == Gender.Female)
                return (StartsWithVowelSound(str) ? "l'" : "la ") + str;
            if (MasculineNeedsLo(str))
                return "lo " + str;
            if (StartsWithVowelSound(str))
                return "l'" + str;
            return "il " + str;
        }

        public override string OrdinalNumber(int number, Gender gender = Gender.None)
        {
            return number + "°";
        }

        public override string Pluralize(string str, Gender gender, int count = -1)
        {
            if (str.NullOrEmpty())
                return str;
            if (TryLookupPluralForm(str, gender, out var plural, count))
                return plural;
            if (count != -1 && count < 2)
                return str;

            char last = str[str.Length - 1];
            if (!IsVowel(last))     // truncated or foreign words (città, gas, computer): invariant
                return str;

            // -io -> -i, collapsing the double i (figlio -> figli, occhio -> occhi)
            if (str.EndsWith("io"))
                return str.Substring(0, str.Length - 2) + "i";

            if (gender == Gender.Female)
            {
                // -ca -> -che, -ga -> -ghe (keeps the hard sound)
                if (str.EndsWith("ca"))
                    return str.Substring(0, str.Length - 2) + "che";
                if (str.EndsWith("ga"))
                    return str.Substring(0, str.Length - 2) + "ghe";
                // -cia / -gia: vowel before -> -cie/-gie ; consonant before -> -ce/-ge
                if (str.EndsWith("cia") || str.EndsWith("gia"))
                {
                    char before = (str.Length >= 4) ? str[str.Length - 4] : '\0';
                    char cg = str[str.Length - 3];   // 'c' or 'g'
                    string stem = str.Substring(0, str.Length - 3) + cg;
                    return stem + (IsVowel(before) ? "ie" : "e");
                }
                // generic -a -> -e
                return str.Substring(0, str.Length - 1) + "e";
            }

            // masculine -ca/-ga -> -chi/-ghi (duca -> duchi, collega -> colleghi)
            if (str.EndsWith("ca"))
                return str.Substring(0, str.Length - 2) + "chi";
            if (str.EndsWith("ga"))
                return str.Substring(0, str.Length - 2) + "ghi";
            // masculine generic: final vowel -> -i
            return str.Substring(0, str.Length - 1) + "i";
        }
    }
}
