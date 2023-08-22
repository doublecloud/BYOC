# Set up BYOC for Google Cloud

To proceed with the BYOC setup:

1. Copy the command from the DoubleCloud **Add external network** dialog.

1. Paste the command to this shell. 

	The command has the following structure: 

	```sh
	./byoc_setup.py -p PROJECT_ID -n NAME -r REGION -c 10.0.0.0/16
	```

	* `PROJECT_ID` is the value from the **ID** field on your project's **Settings** page.
	* `NAME` is the value of the **Name** field from the **Configure network** section of the dialog window.
	* `REGION` is the name of the region from the drop-down menu of the dialog window.

**Recover the output**:

If you missed the output, run the following:

```sh
./byoc_setup.py -n NAME -o -p PROJECT_ID
```

**Delete created resources**:

To delete the created resources, run the following:

```sh
./byoc_setup.py -n NAME -p PROJECT_ID -d
```
