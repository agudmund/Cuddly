using UnityEngine;
using System;

public class Spawn : MonoBehaviour
{
    GameController ctrl;
    Transform currentChute;
    private void Awake()
    {
        ctrl = GameObject.FindGameObjectWithTag("GameController").GetComponent<GameController>();
        currentChute = ctrl.leftSpawn;
    }

    private void OnMouseDown()
    {
        GameObject current = Instantiate(ctrl.components[UnityEngine.Random.Range(0, ctrl.components.Length)], currentChute.transform.position, Quaternion.identity);

        current.GetComponent<Egg>().index = setIndex();



        currentChute = currentChute == ctrl.leftSpawn ? ctrl.rightSpawn : ctrl.leftSpawn;

    }

    int setIndex()
    {
        GameObject[] eggs = GameObject.FindGameObjectsWithTag("Egg");

        float num = (float)eggs.Length / 2;

        return (int)Math.Ceiling(num);
    }
}
