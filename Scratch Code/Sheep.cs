using UnityEngine;
using UnityEngine.AI;
using VikingCrewTools.UI;

public class Sheep : MonoBehaviour
{
    public bool mingling,pushing;
    public GameObject[] targets;
    GameObject target;
    Gate gate = new Gate();
    GameController ctrl;
    public GameObject geo;
    GameObject cube;
    public Exist exist;

    public int damp = 5;

    // States
    public bool gated;
    public bool bored;
    float patience;

    void Start ()
    {
        exist = GetComponent<Exist>();
        transform.name = NamePicker.names[Random.Range(0, NamePicker.names.Length)];
        mingling = true;

        cube = GameObject.FindGameObjectWithTag("Player");
        targets = GameObject.FindGameObjectsWithTag("Spawnling");
        ctrl = GameObject.FindGameObjectWithTag("GameController").GetComponent<GameController>();
	}

    public void newTarget()
    {
        if (!gated)
        {
            string attention = actionEvents[Random.Range(0, actionEvents.Length)];
            targets = GameObject.FindGameObjectsWithTag(attention);

            if (attention == "Spawnling")
            {
                if (targets.Length > 1)
                {
                    target = targets[Random.Range(0, targets.Length)];
                    if (target.GetComponent<Sheep>().gated)
                    {
                        newTarget();
                        return;
                    }
                }
                bubbleCtrl("!", transform, Vector3.zero);
            }
            else if (attention == "Well")
            {
                target = targets[0];
            }
            else if (attention == "Restling")
            {
                target = targets[0];
            }

            exist.busy = true;
        }
        GetComponent<NavMeshAgent>().SetDestination(target.transform.position);
        GetComponent<NavMeshAgent>().speed = exist.speed;
    }
        
    

    public void bubbleCtrl(string message, Transform bub, Vector3 offset)
    {
          SpeechBubbleBehaviour x = SpeechBubbleManager.Instance.AddSpeechBubble
            (
                new Vector3(bub.position.x + offset.x, bub.position.y + 7 + offset.y, bub.position.z + offset.z),
                message,
                mood[Random.Range(0,mood.Length)],
                1
            );
        x.sheep = transform;
    }

    void Update ()
    {
        if (gated)
        {
            if(Time.time - patience > 2)
            {
                bubbleCtrl(goodMorningMessages[Random.Range(0,goodMorningMessages.Length)], transform, Vector3.zero);
                GetComponent<NavMeshAgent>().SetDestination(gate.Marker);
                GetComponent<NavMeshAgent>().speed = exist.speed/3;
                patience = Time.time;
            }
        }

        if (!gated)
        {
            if (Vector3.Distance(transform.position, gate.Marker) < 2f)
            {
                ctrl.score++;
                gated = true;
                patience = Time.time;
            }
        }

        if (target != null)
        {
            if (!gated)
            {
                if (target.tag == "Spawnling")
                {
                    if (Vector3.Distance(transform.position, target.transform.position) < 3.5f)
                    {
                        GetComponent<NavMeshAgent>().speed = 0;
                        float r = geo.GetComponent<Renderer>().material.color.r;
                        float g = geo.GetComponent<Renderer>().material.color.g;
                        float b = geo.GetComponent<Renderer>().material.color.b;
                        float rt = target.GetComponent<Sheep>().geo.GetComponent<Renderer>().material.color.r;
                        float gt = target.GetComponent<Sheep>().geo.GetComponent<Renderer>().material.color.g;
                        float bt = target.GetComponent<Sheep>().geo.GetComponent<Renderer>().material.color.b;

                        float rs = (r + rt) / 2.0f;
                        float gs = (g + gt) / 2.0f;
                        float bs = (b + bt) / 2.0f;

                        Color settings = new Color(rs, gs, bs);

                        geo.GetComponent<Renderer>().material.color = settings;
                        exist.busy = false;
                    }
                }
                else if(target.tag == "Well")
                {
                    if (Vector3.Distance(transform.position, target.transform.position) < 10f)
                    {
                        GetComponent<NavMeshAgent>().speed = 0;
                        exist.busy = false;
                    }
                }
                else if (target.tag == "Restling")
                {
                    if (Vector3.Distance(transform.position, target.transform.position) < 10f)
                    {
                        GetComponent<NavMeshAgent>().speed = 0;
                        exist.busy = false;
                    }
                }
            }
        }
    }

    SpeechBubbleManager.SpeechbubbleType[] mood = new SpeechBubbleManager.SpeechbubbleType[]
    {
        SpeechBubbleManager.SpeechbubbleType.NORMAL,
        SpeechBubbleManager.SpeechbubbleType.THINKING,
        SpeechBubbleManager.SpeechbubbleType.SERIOUS,
        SpeechBubbleManager.SpeechbubbleType.ANGRY
    };

    string[] goodMorningMessages = new string[]
    {
        "yum yum",
        "Is the grass yum yum?",
        "Am I yum yum?"
    };

    string[] actionEvents = new string[]
    {
        "Spawnling",
        "Well",
        "Restling"
    };
}
