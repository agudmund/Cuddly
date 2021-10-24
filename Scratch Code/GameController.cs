using System.Collections;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.AI;

public class GameController : MonoBehaviour
{
    public GameObject spawnPoint;
    public GameObject spawnling;
    public GameObject well;
    public Text scorings;
    public int score = 0;

    void Start ()
    {
        StartCoroutine(Spawn());
	}
	
	void Update ()
    {
        scorings.text = "Happy Sheep: " + score.ToString();
	}

    IEnumerator Spawn()
    {
        while (true)
        {
            GameObject current = Instantiate(spawnling, spawnPoint.transform.position+Vector3.up*3, Quaternion.identity);
            current.GetComponent<NavMeshAgent>().SetDestination(well.transform.position);
            yield return new WaitForSeconds(5);
        }
    }
}
