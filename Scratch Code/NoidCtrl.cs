using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.AI;

public class NoidCtrl : MonoBehaviour {

    public Transform target;
    NavMeshAgent nav;

	void Start ()
    {
        nav = GetComponent<NavMeshAgent>();
        target = GameObject.FindGameObjectWithTag("Player").GetComponent<Transform>();
	}
	
	void Update ()
    {
        nav.SetDestination(target.position);	
	}
}
