using UnityEngine;

public class PixelPicker : MonoBehaviour
{
    Camera cam;
    RaycastHit hit;
    public GameObject cube;
    public bool movecamwithpointer;
    public Vector3 hitpoint;

    void Start()
    {
        cam = GetComponent<Camera>();
    }

    void Update()
    {
        if (ValidateHit())
        {
            hitpoint = hit.point;
            if (movecamwithpointer == true)
            {
                MoveCam();
            }
        }
    }

    void MoveCam()
    {
        float lookX = hit.point.x;
        float lookZ = hit.point.z;
        if (lookX > 15)
        {
            lookX = 15;
        }
        if (lookX < -15)
        {
            lookX = -15;
        }

        if (lookZ < -10)
        {
            lookZ = -10;
        }
        if (lookZ > 15)
        {
            lookZ = 15;
        }

        if (transform.position.x - lookX < -10 ||
            transform.position.x - lookX > 10
            )
        {
            Vector3 newPos = new Vector3(
                    lookX,
                    90,
                    lookZ
                    );
            transform.position = Vector3.Lerp(transform.position, newPos, .01f);
        }

        if (transform.position.z - lookZ < -10 ||
            transform.position.z - lookZ > 10
            )
        {
            Vector3 newPos = new Vector3(
                    lookX,
                    90,
                    lookZ
                    );
            transform.position = Vector3.Lerp(transform.position, newPos, .01f);
        }
    }

    bool ValidateHit()
    {
        if (!Physics.Raycast(cam.ScreenPointToRay(Input.mousePosition), out hit))
        {
            return false;
        }

        MeshCollider meshCollider = hit.collider as MeshCollider;
        if (meshCollider == null || meshCollider.sharedMesh == null)
            return false;

        return true;
    }
}