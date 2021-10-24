using UnityEngine;
using UnityEngine.AI;

public class Player : MonoBehaviour
{
    public GameObject ray;
    Gate gate = new Gate();
    Collider otherling;

    private void OnTriggerEnter(Collider other)
    {
        if (other.gameObject.tag == "Spawnling")
        {
            other.gameObject.tag = "Herding";
            Sheep sheep = other.GetComponent<Sheep>();
            NavMeshAgent nav = other.GetComponent<NavMeshAgent>();
            if (!sheep.gated)
            {
                sheep.bubbleCtrl("x", other.transform, Vector3.zero);
                nav.SetDestination(gate.Marker);
                if (sheep.exist)
                {
                    nav.speed = sheep.exist.speed;
                }
            }
        }
    }

    private void OnTriggerStay(Collider other)
    {
        if (other.gameObject.tag == "Spawnling")
        {
            NavMeshAgent nav = other.GetComponent<NavMeshAgent>();
            if (nav.destination != gate.Marker)
            {
                nav.SetDestination(gate.Marker);
            }
        }
    }

    private void OnTriggerExit(Collider other)
    {
        if (other.gameObject.tag == "Herding")
        {
            other.gameObject.tag = "Spawnling";
            Sheep sheep = other.GetComponent<Sheep>();
            sheep.exist.busy = false;
            NavMeshAgent nav = other.GetComponent<NavMeshAgent>();
            nav.speed = 0;
        }
    }

    private void Update()
    {
        GameObject[] others = GameObject.FindGameObjectsWithTag("Herding");

        if (Input.GetButton("Fire1"))
        {
            ray.GetComponent<Light>().intensity = 25;
            // push with click
            foreach (GameObject otherling in others)
            {
                if (!otherling.GetComponent<Sheep>().gated)
                {
                    int rotationSpeed = 15;
                    Vector3 direction = ((otherling.transform.position - transform.position).normalized) / 20 ;
                    Quaternion lookRotation = Quaternion.LookRotation(new Vector3(direction.x, 0, direction.z));
                    transform.rotation = Quaternion.Slerp(transform.rotation, lookRotation, Time.deltaTime * rotationSpeed);
                    otherling.GetComponent<NavMeshAgent>().Move(direction);
                }
            }
        }
        if (Input.GetButtonUp("Fire1"))
        {
            ray.GetComponent<Light>().intensity = 0;
        }
    }
}
