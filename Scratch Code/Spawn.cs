using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Spawn : MonoBehaviour {

    public GameObject Noid;

    IEnumerator Spawnling()
    {
        while (true)
        {
            Instantiate(Noid,transform.position,Quaternion.identity);
            yield return new WaitForSeconds(2);
        }
    }

	// Use this for initialization
	void Start ()
    {
        StartCoroutine(Spawnling());
		
	}
	
	// Update is called once per frame
	void Update () {
		
	}
}
