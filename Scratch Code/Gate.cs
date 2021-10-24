using UnityEngine;

public class Gate : MonoBehaviour
{
    public GameObject[] points;

    public Vector3 Marker
    {
        get{
            points = GameObject.FindGameObjectsWithTag("Finish");
            GameObject x = points[Random.Range(0, points.Length)];
            return x.transform.position ;
        }
    }
}
