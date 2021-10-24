using UnityEngine;

public class Hatch : MonoBehaviour
{
    GameObject[] eggs;
    GameController ctrl;

    private void Awake()
    {
        ctrl = GameObject.FindGameObjectWithTag("GameController").GetComponent<GameController>();
    }

    private void OnMouseDown()
    {
        eggs = GameObject.FindGameObjectsWithTag("Egg");
        foreach(GameObject egg in eggs)
        {
            if(egg.GetComponent<Egg>().index == 1)
            {
                Destroy(egg);
            }
            else
            {
                egg.GetComponent<Egg>().index--;
            }

        }
        Instantiate(ctrl.duddly);
    }
}
