# Cubic ERP 2020

Cubic ERP Community Edition is a suite of open source apps for business and government processes, available on mobile & web devices, based on LGPL license.

CubicERP Peru S.R.L is the company that lead this project, our experience in ERP software started in 2009 with TeraData SAC, having served multinational corporations, large companies and small businesses throughout Latin America, providing training services, consulting and software development. 

Contact us at http://cubicerp.com.

## Quick Start

### Prerequisites

First install Docker from https://docs.docker.com/engine/install/

### Run

    $ docker run --restart=always --name cubicerp-ce \
        -v cubicerp-ce-base:/var/lib/postgresql \
        -v cubicerp-ce-data:/home/cubicerp/ecbc/data \
        -v cubicerp-ce-conf:/home/cubicerp/ecbc/config \
        -dit -p 8069:8069 cubicerp/cubicerp

### Test

    http://localhost:8069

## Useful Links

* Help to Users: https://cubicerp.com/help
* New Features & Bugs: https://cubicerp.com/issues
* Mailing List: https://groups.google.com/forum/#!forum/cubicerp
* Demo: http://demo.cubicerp.com/web - User: demo, Password: demo
