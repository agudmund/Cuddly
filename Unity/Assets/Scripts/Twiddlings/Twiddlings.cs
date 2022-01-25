using UnityEngine;
using UnityEngine.AI;

public class Twiddlings : MonoBehaviour
{
    public Transform target;
    NavMeshAgent nav;

    void Start()
    {
        nav = GetComponent<NavMeshAgent>();
        SetTarget();
    }

    void SetTarget()
    {
        nav.SetDestination(target.position);
    }

    public string[] CharacterType = new string[]
    {
        "Alpha",        // Other wuddlies tend to flock and follow whatever this one does.
        "Autist",       // Rarely performs actions without a certain proximity distance from others.
        "Bravo",        // Agressive, main Fuddly trait.
        "Caregiver",    // has a tendency to pause own tasks to perform tasks of others.  Main Cuddly Trait.
        "Cub",          // Lower stats and rarely alone.
        "Competitor",   // Boosted skills if more characters are aiming for same goal.
        "Confidant",    // Boosts skills of those around him.
        "Conformist",   // Works best in a pack.
        "Conniver",     // Swindler and a Thief.
        "Curmudgeon",   // Boosted skills when others fail.
        "Deviant",      // Only performs tasks alone, otherwise sabotages tasks.
        "Director",     // Everyone gets boosted skills.
        "Fanatic",      // Massive boosted skills on trained actions.
        "Gallant",      // Only receives skill upgrades if other character sees them complete it.
        "Jester",       // Main Duddly Trait.  Everyone pauses their tasks sporadically as he flails.
        "Judge",        
        "Lone Wolf",
        "Maker",
        "Martyr",
        "Masochist",
        "Penitent",
        "Predator",
        "Rebel",
        "Reluctant",
        "Reveler",
        "Show-Off",
        "Survivor",
        "Traditionalist",
        "Visionary"
    };
}
