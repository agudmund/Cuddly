using UnityEngine;
using UnityEngine.AI;

public class Behave : MonoBehaviour
{
    bool bored,fixing,fetching,clicking,cleaning;
    float boredTimer;
    GameObject respawn,ctrl;
    Vector3 loc;

    //Item button;
    NavMeshAgent agent;
    //NavCtrl navCtrl;
    Spawn spawn;

    public GameObject boothBase,lightGlow;
    GameObject[] fixables;

    private void Start()
    {
        /*
        ctrl = GameObject.FindGameObjectWithTag("GameController");
        respawn = GameObject.FindGameObjectWithTag("Respawn");
        boothBase = GameObject.FindGameObjectWithTag("test");
        agent = this.GetComponent<NavMeshAgent>();
        navCtrl = this.GetComponent<NavCtrl>();
        spawn = ctrl.GetComponent<Spawn>();
        button = respawn.GetComponent<Item>();

        light = lightGlow.GetComponent<Light>();
        
        boredTimer = Time.time;
        */
    }

    string[] things = new[]
    {
        "fetch",
        "push",
        "remove",
        "fix"
    };

    string action()
    {
        return things[Random.Range(0, things.Length)];
    }

    private void Update()
    {
        
        if (fixing)
        {
            FixRespawn();
        }

        if (clicking)
        {
            ClickRespawn();
        }

        if (fetching)
        {
            CollectBox();
        }

        if (cleaning)
        {
            Clean();
        }
    }

    void Bored ()
    {
        bored = false;
        boredTimer = Time.time;
        string act = action();
        if (act == "fetch")
        {
            fetching = true;
        }
        if(act == "push")
        {
            clicking = true;
        }
        if (act == "remove")
        {
            cleaning = true;
        }
        if (act == "fix")
        {
            fixing = true;
        }
        if(act == "remove")
        {
            cleaning = true;
        }
    }

    void Clean()
    {
        GameObject[] targets = GameObject.FindGameObjectsWithTag("scrap");
        GameObject scrapHome = GameObject.FindGameObjectWithTag("scrapBase");

        /*
        if (targets.Length > 0)
        {
            PickTarget(targets);
            if (navCtrl.currentTarget)
            {
                if (Vector3.Distance(transform.position, navCtrl.currentTarget.transform.position) < 1.5f)
                {
                    if (navCtrl.currentTarget.tag == "scrap")
                    {
                        navCtrl.currentTarget.GetComponent<Rigidbody>().isKinematic = true;
                        navCtrl.currentTarget.transform.parent = transform;
                        navCtrl.currentTarget = scrapHome;
                    }
                }
            }
        }
        else
        {
            cleaning = false;
            busy = false;
        }
        */
    }
    
    void CollectBox()
    {
        GameObject[] targets = GameObject.FindGameObjectsWithTag("brick");

        if (targets.Length > 0)
        {
            //Bubble("I see boxes");
        }
        else
        {
            
            fetching = false;
        }
    }

    void FixRespawn()
    {
        /*
        if (button.assignee == 0)
        {
            if (button.outOfBounds)
            {
                Bubble("Should fix that spawner");
                button.assignee = id;
                navCtrl.currentTarget = respawn;
            } }

        else if(button.assignee == id)
        { 
                if (Vector3.Distance(transform.position, respawn.transform.position) < 1.5f)
                {
                    respawn.GetComponent<Rigidbody>().isKinematic = true;
                    respawn.transform.parent = transform;
                    navCtrl.currentTarget = boothBase;
                }
                else
                {
                    navCtrl.currentTarget = respawn;
                }
        }
        if(!button.outOfBounds)
        {
            respawn.GetComponent<Rigidbody>().isKinematic = false;
            button.assignee = 0;
            respawn.transform.parent = null;
            fixing = false;
            busy = false;
        }
        */
        
    }

    public void ClickRespawn()
    {
        /*
        navCtrl.currentTarget = respawn;
        if (Vector3.Distance(transform.position, respawn.transform.position) < 2f)
        {
            navCtrl.currentTarget = null;

            Bubble("Clicking");
            GameObject[] boxes = GameObject.FindGameObjectsWithTag("brick");
            GameObject[] players = GameObject.FindGameObjectsWithTag("Player");

            if (!button.outOfBounds)
            {
                if (boxes.Length < players.Length * 2)
                {
                    spawn.Materialize();
                    clicking = false;
                    busy = false;
                }
                else
                {
                    clicking = false;
                    fetching = true;
                }
            }
            else
            {
                clicking = false;
                fixing = true;
            }
            
        }*/
    }
}
