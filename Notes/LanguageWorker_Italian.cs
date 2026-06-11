// ============================================================================
// RIFERIMENTO DECOMPILATO — questo file NON viene caricato dal language pack.
//
// Sorgente : Assembly-CSharp.dll  (RimWorld 1.6.4850 rev645)
// Tipo     : Verse.LanguageWorker_Italian
// Strumento: ILSpy (ilspycmd)
//
// Questa classe è GIÀ compilata dentro il gioco: il file serve solo come
// documentazione/riferimento, esattamente come i .cs di francese e spagnolo nei
// rispettivi repo. Un language pack (solo dati) NON può sostituire un LanguageWorker.
// Per modificarne il comportamento serve una PR upstream a Ludeon, oppure un mod
// companion con assembly compilato (es. patch Harmony).
//
// Spiegazione e limiti noti: docs/GENERAZIONE-NOMI-E-GRAMMATICA.md
// ============================================================================

namespace Verse;

public class LanguageWorker_Italian : LanguageWorker
{
	public override string WithIndefiniteArticle(string str, Gender gender, bool plural = false, bool name = false)
	{
		if (str.NullOrEmpty())
		{
			return str;
		}
		if (name)
		{
			return str;
		}
		char c = str[0];
		char c2 = ((str.Length >= 2) ? str[1] : '\0');
		if (gender == Gender.Female)
		{
			if (IsVowel(c))
			{
				return "un'" + str;
			}
			return "una " + str;
		}
		char c3 = char.ToLower(c);
		char c4 = char.ToLower(c2);
		if ((c == 's' || c == 'S') && !IsVowel(c2))
		{
			return "uno " + str;
		}
		if ((c3 == 'p' && c4 == 's') || (c3 == 'p' && c4 == 'n') || c3 == 'z' || c3 == 'x' || c3 == 'y' || (c3 == 'g' && c4 == 'n'))
		{
			return "uno " + str;
		}
		return "un " + str;
	}

	public override string WithDefiniteArticle(string str, Gender gender, bool plural = false, bool name = false)
	{
		if (str.NullOrEmpty())
		{
			return str;
		}
		if (name)
		{
			return str;
		}
		char c = str[0];
		char ch = ((str.Length >= 2) ? str[1] : '\0');
		if (gender == Gender.Female)
		{
			if (IsVowel(c))
			{
				return "l'" + str;
			}
			return "la " + str;
		}
		switch (c)
		{
		case 'Z':
		case 'z':
			return "lo " + str;
		case 'S':
		case 's':
			if (!IsVowel(ch))
			{
				return "lo " + str;
			}
			break;
		}
		if (IsVowel(c))
		{
			return "l'" + str;
		}
		return "il " + str;
	}

	public bool IsVowel(char ch)
	{
		return "aeiouAEIOU".IndexOf(ch) >= 0;
	}

	public override string OrdinalNumber(int number, Gender gender = Gender.None)
	{
		return number + "°";
	}

	public override string Pluralize(string str, Gender gender, int count = -1)
	{
		if (str.NullOrEmpty())
		{
			return str;
		}
		if (TryLookupPluralForm(str, gender, out var plural, count))
		{
			return plural;
		}
		if (count != -1 && count < 2)
		{
			return str;
		}
		char ch = str[str.Length - 1];
		if (!IsVowel(ch))
		{
			return str;
		}
		if (gender == Gender.Female)
		{
			return str.Substring(0, str.Length - 1) + "e";
		}
		return str.Substring(0, str.Length - 1) + "i";
	}
}
