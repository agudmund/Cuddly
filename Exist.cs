using System.Collections;
using UnityEngine;
using UnityEngine.AI;

public class Exist : MonoBehaviour
{
    NavMeshAgent nav;
    Sheep sheep;
    Renderer ren;
    Color basecolor;
    public float energy, speed;
    Transform resting;
    Transform target;
    
    // states
    bool lookingforrest;
    bool sleeping;
    public bool busy;
    public bool idle;
    public bool moral;

    float timer = 5;

    private void Awake()
    {
        resting = GameObject.FindGameObjectWithTag("Restling").GetComponent<Transform>();
        nav = GetComponent<NavMeshAgent>();
        sheep = GetComponent<Sheep>();
        ren = sheep.geo.GetComponent<Renderer>();
        basecolor = ColorPickers.col[Random.Range(0, ColorPickers.col.Length)];
        idle = true;
    }

    void Start()
    {
        ren.material.color = basecolor;
        energy = Random.Range(5, 12);
        speed = Random.Range(0.1f, 1) * 10;
        nav.acceleration = Random.Range(0.1f, 1) * energy;
    }

    private void Update()
    {
        if (!busy)
        {
            timer = timer - Time.deltaTime;
            if (timer < 0)
            {
                sheep.newTarget();
                timer = 5;
                busy = true;
            }
        }
    }

    /*
    private void Update()
    {
        nav.speed = speed * energy;
        if (Vector3.Distance(transform.position, resting.position) < 5)
        {
            if (!sleeping && lookingforrest)
            {
                nav.velocity = Vector3.zero;
                StartCoroutine(Sleep());
            }
        }
    }
    */

    public IEnumerator ExistanZe()
    {
        while (!sleeping)
        {
            energy -= .3f;

            if (energy > 2)
            {
                if (idle && !moral)
                {
                    moral = true;
                    idle = false;
                    sheep.newTarget();
                }
            }

            if (energy < 2)
            {
                if (!lookingforrest)
                {
                    nav.SetDestination(resting.position);
                    idle = false;
                    lookingforrest = true;
                }
            }
            if (energy < 1)
            {
                energy = 0;
                StartCoroutine(Sleep());
                break;
            }

            float waittime = Random.Range(.5f, 2);
            yield return new WaitForSeconds(waittime);

        }
    }
    
    IEnumerator Sleep()
    {
        sheep.bubbleCtrl("zZZ", transform, Vector3.zero);
        sleeping = true;
        lookingforrest = false;
        idle = false;
        nav.ResetPath();
        nav.speed = 0;
        while (sleeping)
        {
            energy += 1;
            if (energy > Random.Range(6, 11))
            {
                if (sleeping)
                {
                    sleeping = false;
                    StartCoroutine(ExistanZe());
                    idle = true;
                    moral = false;
                    break;
                }
            }
            float waittime = Random.Range(.5f, 2);
            yield return new WaitForSeconds(waittime);
        }
    }
}

