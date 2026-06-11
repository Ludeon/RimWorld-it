// ============================================================================
//  LanguageWorker_Italian — versione MIGLIORATA (proposta)
// ============================================================================
//
//  Base: Verse.LanguageWorker_Italian decompilato da Assembly-CSharp.dll
//        (RimWorld 1.6.4850). Vedi docs/GENERAZIONE-NOMI-E-GRAMMATICA.md per il
//        comportamento originale e i suoi limiti.
//
//  ⚠️  DEPLOYMENT — leggere prima di aspettarsi effetti in gioco:
//      Un language pack è SOLO DATI: questo .cs NON viene caricato dal gioco per
//      il solo fatto di stare nel repo. Il gioco usa il suo LanguageWorker_Italian
//      compilato nella DLL. Per far valere queste migliorie:
//        (a) PR upstream a Ludeon (lo compilano loro nel gioco) — consigliato per
//            la traduzione ufficiale; questo file è già pronto allo scopo; oppure
//        (b) mod companion con assembly compilato: o una patch Harmony che fa
//            override dei metodi di Verse.LanguageWorker_Italian, o una classe con
//            NOME DIVERSO referenziata da LanguageInfo.xml (languageWorkerClass).
//
//  MIGLIORIE rispetto al worker di serie:
//   1. Articolo determinativo "lo": ora anche per gn, ps, pn, x, y, i+vocale
//      (lo gnomo, lo psicologo, lo pneumatico, lo xilofono, lo yogurt, lo iato).
//      Il worker di serie dava "il psicologo" / "il gnomo" (sbagliato).
//   2. Articoli al PLURALE (prima ignorati del tutto): i/gli/le e partitivi dei/degli/delle.
//   3. Plurali femminili: -ca→-che, -ga→-ghe (amica→amiche, collega→colleghe) e
//      -cia/-gia→-cie/-gie o -ce/-ge a seconda della lettera precedente
//      (camicia→camicie, faccia→facce). I plurali irregolari restano gestiti
//      dalle liste esplicite (TryLookupPluralForm) + WordInfo/Gender.
//
// ============================================================================

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

        // Vero se la parola maschile richiede "lo / uno / gli / degli":
        // s impura (s+consonante), z, x, y, ps, pn, gn, i + vocale (semiconsonante).
        private bool MasculineNeedsLo(string str)
        {
            char c0 = char.ToLower(str[0]);
            char c1 = (str.Length >= 2) ? char.ToLower(str[1]) : '\0';
            bool secondIsVowel = (str.Length >= 2) && IsVowel(str[1]);

            if (c0 == 'z' || c0 == 'x' || c0 == 'y')
                return true;
            if (c0 == 's' && !secondIsVowel)        // s impura
                return true;
            if (c0 == 'p' && (c1 == 's' || c1 == 'n'))  // ps, pn
                return true;
            if (c0 == 'g' && c1 == 'n')              // gn
                return true;
            if (c0 == 'i' && secondIsVowel)          // i + vocale: lo iato, lo ione
                return true;
            return false;
        }

        public override string WithIndefiniteArticle(string str, Gender gender, bool plural = false, bool name = false)
        {
            if (str.NullOrEmpty() || name)
                return str;

            char c = str[0];

            if (plural)   // partitivo: dei / degli / delle
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
            if (!IsVowel(last))     // parole tronche o straniere (città, gas, computer): invariate
                return str;

            if (gender == Gender.Female)
            {
                // -ca -> -che, -ga -> -ghe (mantiene il suono duro)
                if (str.EndsWith("ca"))
                    return str.Substring(0, str.Length - 2) + "che";
                if (str.EndsWith("ga"))
                    return str.Substring(0, str.Length - 2) + "ghe";
                // -cia / -gia: vocale prima -> -cie/-gie ; consonante prima -> -ce/-ge
                if (str.EndsWith("cia") || str.EndsWith("gia"))
                {
                    char before = (str.Length >= 4) ? str[str.Length - 4] : '\0';
                    char cg = str[str.Length - 3];   // 'c' o 'g'
                    string stem = str.Substring(0, str.Length - 3) + cg;
                    return stem + (IsVowel(before) ? "ie" : "e");
                }
                // generico -a -> -e
                return str.Substring(0, str.Length - 1) + "e";
            }

            // maschile: -o/-e + vocale -> -i
            return str.Substring(0, str.Length - 1) + "i";
        }
    }
}
