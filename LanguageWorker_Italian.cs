// LanguageWorker_Italian — improved article and plural handling.
//
// Changes over the previous version:
//   1. Definite article "lo" now also applies to words starting with gn, ps, pn,
//      x, y, and i+vowel (lo gnomo, lo psicologo, lo pneumatico, lo xilofono,
//      lo yogurt, lo iato). Previously these produced "il psicologo" / "il gnomo".
//   2. Plural articles are now handled (previously they fell through to the
//      singular forms): i/gli/le and the partitives dei/degli/delle.
//   3. Feminine plurals: -ca -> -che, -ga -> -ghe (amica -> amiche, collega ->
//      colleghe) and -cia/-gia -> -cie/-gie or -ce/-ge depending on the preceding
//      letter (camicia -> camicie, faccia -> facce). Irregular plurals remain
//      handled by TryLookupPluralForm and the WordInfo gender data.

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

            char c = str[0];

            if (plural)   // partitive: dei / degli / delle
            {
                if (gender == Gender.Female)
                    return "delle " + str;
                return ((MasculineNeedsLo(str) || IsVowel(c)) ? "degli " : "dei ") + str;
            }

            if (gender == Gender.Female)
                return (IsVowel(c) ? "un'" : "una ") + str;
            if (MasculineNeedsLo(str))
                return "uno " + str;
            return "un " + str;
        }

        public override string WithDefiniteArticle(string str, Gender gender, bool plural = false, bool name = false)
        {
            if (str.NullOrEmpty() || name)
                return str;

            char c = str[0];

            if (plural)   // i / gli / le
            {
                if (gender == Gender.Female)
                    return "le " + str;
                return ((MasculineNeedsLo(str) || IsVowel(c)) ? "gli " : "i ") + str;
            }

            if (gender == Gender.Female)
                return (IsVowel(c) ? "l'" : "la ") + str;
            if (MasculineNeedsLo(str))
                return "lo " + str;
            if (IsVowel(c))
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

            // masculine: -o/-e + vowel -> -i
            return str.Substring(0, str.Length - 1) + "i";
        }
    }
}
