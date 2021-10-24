using UnityEngine;

public class LookAtTarget : MonoBehaviour
{
    public Transform target;
    public Vector3 followAngles;
    public Vector2 rotationRange;
    public float followSpeed = 1;
    
    Quaternion startRotation;
    Vector3 followVelocity = new Vector3(25, 25, 25);

    void Start () {
        startRotation = transform.localRotation;
    }
	
	void Update ()
    {
        transform.localRotation = startRotation;
        Vector3 localTarget = transform.InverseTransformPoint(target.position);
        float yAngle = Mathf.Atan2(localTarget.x, localTarget.z) * Mathf.Rad2Deg;

        yAngle = Mathf.Clamp(yAngle, -rotationRange.y * 0.5f, rotationRange.y * 0.5f);
        transform.localRotation = startRotation * Quaternion.Euler(0, yAngle, 0);

        localTarget = transform.InverseTransformPoint(target.position);
        float xAngle = Mathf.Atan2(localTarget.y, localTarget.z) * Mathf.Rad2Deg;
        xAngle = Mathf.Clamp(xAngle, -rotationRange.x * 0.5f, rotationRange.x * 0.5f);
        
        var targetAngles = new Vector3(followAngles.x + Mathf.DeltaAngle(followAngles.x, xAngle),
                                       followAngles.y + Mathf.DeltaAngle(followAngles.y, yAngle));
        
        followAngles = Vector3.SmoothDamp(followAngles, targetAngles, ref followVelocity, followSpeed);
        
        transform.localRotation = startRotation * Quaternion.Euler(-followAngles.x, followAngles.y, 0);
    }
}
