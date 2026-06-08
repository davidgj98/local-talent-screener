from __future__ import annotations
import os
from fpdf import FPDF

OUTPUT_DIR = "test_cvs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

profiles = [
    {
        "filename": "v2_andres_martin_data.pdf",
        "name": "Andrés Martín López",
        "email": "andres.martin@email.com",
        "years": 6,
        "techs": [
            "Python",
            "Pandas",
            "NumPy",
            "FastAPI",
            "SQL",
            "PostgreSQL",
            "Apache Spark",
            "Airflow",
            "Docker",
            "AWS",
            "Kafka",
            "dbt",
            "Terraform",
        ],
        "experience": [
            (
                "Senior Data Engineer",
                "FintechData",
                "2022-2026",
                "Architected data pipelines on AWS with Airflow and Spark. Data warehouse modeling with dbt on Redshift. Streaming with Kafka for transactional data.",
            ),
            (
                "Data Engineer",
                "BankAnalytics",
                "2020-2022",
                "Developed ETLs with Airflow and Python. SQL query optimization on PostgreSQL. Deployment with Docker on AWS ECS.",
            ),
            (
                "Junior Data Engineer",
                "DataStartup",
                "2018-2020",
                "Data cleaning and transformation with Pandas. Batch process automation with Python scripts.",
            ),
        ],
        "education": "MSc in Data Engineering — Universidad Politécnica de Madrid",
        "certifications": [
            "AWS Certified Data Analytics",
            "dbt Analytics Engineering Certification",
        ],
        "languages": ["Spanish (native)", "English C1"],
    },
    {
        "filename": "v2_beatriz_garcia_data.pdf",
        "name": "Beatriz García Ruiz",
        "email": "beatriz.garcia@email.com",
        "years": 5,
        "techs": [
            "Python",
            "Pandas",
            "SQL",
            "BigQuery",
            "Apache Spark",
            "Airflow",
            "Prefect",
            "Docker",
            "GCP",
            "Kafka",
            "scikit-learn",
        ],
        "experience": [
            (
                "Data Engineer",
                "CloudDataCorp",
                "2021-2026",
                "Built data pipelines on GCP with Prefect and Dataflow. Data processing with Spark on Dataproc. Streams with Kafka and Pub/Sub.",
            ),
            (
                "Data Analyst",
                "RetailData",
                "2019-2021",
                "Data analysis with Pandas and SQL. Looker dashboards. Report automation with Airflow.",
            ),
        ],
        "education": "BSc in Computer Science — Universidad de Barcelona",
        "certifications": ["Google Cloud Professional Data Engineer"],
        "languages": ["Spanish (native)", "English C1", "Catalan (native)"],
    },
    {
        "filename": "v2_carlos_mendez_data.pdf",
        "name": "Carlos Méndez Sánchez",
        "email": "carlos.mendez@email.com",
        "years": 5,
        "techs": [
            "Python",
            "Pandas",
            "SQL",
            "PostgreSQL",
            "Airflow",
            "Docker",
            "AWS",
            "scikit-learn",
            "MLflow",
            "FastAPI",
        ],
        "experience": [
            (
                "Data Engineer",
                "HealthDataTech",
                "2022-2026",
                "ETL pipelines with Airflow and Python for healthcare data. FastAPI APIs for serving ML models. Deployment on AWS ECS with Docker.",
            ),
            (
                "Data Scientist",
                "PredictiveAnalytics",
                "2020-2022",
                "Predictive models with scikit-learn. Feature engineering with Pandas. Automation with MLflow.",
            ),
        ],
        "education": "MSc in Data Science — Universidad Carlos III",
        "certifications": ["AWS Certified Machine Learning Specialty"],
        "languages": ["Spanish (native)", "English B2"],
    },
    {
        "filename": "v2_diana_fernandez_data.pdf",
        "name": "Diana Fernández Torres",
        "email": "diana.fernandez@email.com",
        "years": 4,
        "techs": [
            "Python",
            "Pandas",
            "SQL",
            "MySQL",
            "Airflow",
            "Docker",
            "AWS",
            "Tableau",
            "dbt",
        ],
        "experience": [
            (
                "Data Engineer",
                "EcommerceData",
                "2022-2026",
                "Developed ETL pipelines with Airflow. Data modeling with dbt. Analytical dashboards in Tableau.",
            ),
            (
                "Data Analyst",
                "MarketingAnalytics",
                "2020-2022",
                "Data analysis with SQL and Python. Report and dashboard creation. Extraction automation.",
            ),
        ],
        "education": "BSc in Statistics — Universidad de Valencia",
        "certifications": ["dbt Fundamentals"],
        "languages": ["Spanish (native)", "English B2"],
    },
    {
        "filename": "v2_eduardo_lozano_data.pdf",
        "name": "Eduardo Lozano Jiménez",
        "email": "eduardo.lozano@email.com",
        "years": 7,
        "techs": [
            "Python",
            "Django",
            "PostgreSQL",
            "Docker",
            "Kubernetes",
            "AWS",
            "Redis",
            "Microservices",
            "CI/CD",
        ],
        "experience": [
            (
                "Backend Engineer",
                "APICorp",
                "2020-2026",
                "Developed microservices with Django and PostgreSQL. Infrastructure on AWS EKS with Docker and Kubernetes. CI/CD pipelines with GitHub Actions.",
            ),
            (
                "Fullstack Developer",
                "WebDev",
                "2018-2020",
                "Web application development with Django and PostgreSQL. Deployment on AWS Elastic Beanstalk.",
            ),
        ],
        "education": "BSc in Systems Engineering — Universidad de Sevilla",
        "certifications": ["AWS Solutions Architect Associate"],
        "languages": ["Spanish (native)", "English C1"],
    },
    {
        "filename": "v2_fatima_ramirez_data.pdf",
        "name": "Fátima Ramírez Navarro",
        "email": "fatima.ramirez@email.com",
        "years": 5,
        "techs": [
            "Python",
            "scikit-learn",
            "TensorFlow",
            "PyTorch",
            "Pandas",
            "SQL",
            "FastAPI",
            "Docker",
            "AWS",
        ],
        "experience": [
            (
                "ML Engineer",
                "AILabs",
                "2021-2026",
                "Developed and deployed ML models with FastAPI and Docker on AWS. Training pipelines with MLflow. Data processing with Pandas.",
            ),
            (
                "Data Scientist",
                "DataScienceCo",
                "2019-2021",
                "Classification and regression models with scikit-learn. ETL with Pandas. Data visualization.",
            ),
        ],
        "education": "MSc in Artificial Intelligence — Universidad de Granada",
        "certifications": ["TensorFlow Developer Certificate"],
        "languages": ["Spanish (native)", "English C1"],
    },
    {
        "filename": "v2_guillermo_torres_data.pdf",
        "name": "Guillermo Torres Molina",
        "email": "guillermo.torres@email.com",
        "years": 6,
        "techs": [
            "Docker",
            "Kubernetes",
            "Terraform",
            "Ansible",
            "AWS",
            "Jenkins",
            "Linux",
            "Bash",
            "Basic Python",
        ],
        "experience": [
            (
                "DevOps Engineer",
                "InfraCloud",
                "2020-2026",
                "Infrastructure management on AWS with Terraform. Kubernetes clusters. CI/CD pipelines with Jenkins.",
            ),
            (
                "SysAdmin",
                "HostingPro",
                "2018-2020",
                "Linux server administration. Automation with Ansible. Monitoring with Prometheus.",
            ),
        ],
        "education": "BSc in Systems Administration — Universidad de Málaga",
        "certifications": ["CKA", "AWS DevOps Engineer"],
        "languages": ["Spanish (native)", "English B2"],
    },
    {
        "filename": "v2_helena_dominguez_data.pdf",
        "name": "Helena Domínguez Castro",
        "email": "helena.dominguez@email.com",
        "years": 3,
        "techs": [
            "JavaScript",
            "TypeScript",
            "React",
            "Node.js",
            "MongoDB",
            "Express",
            "CSS",
            "Jest",
        ],
        "experience": [
            (
                "Fullstack Developer",
                "WebAgency",
                "2022-2026",
                "Web application development with React and Node.js. REST APIs with Express. MongoDB databases.",
            ),
            (
                "Junior Developer",
                "TechStartup",
                "2021-2022",
                "Frontend development with React. Node.js API maintenance.",
            ),
        ],
        "education": "BSc in Web Development — Universidad de Alicante",
        "certifications": [],
        "languages": ["Spanish (native)", "English B1"],
    },
    {
        "filename": "v2_ignacio_prieto_data.pdf",
        "name": "Ignacio Prieto Herrera",
        "email": "ignacio.prieto@email.com",
        "years": 9,
        "techs": [
            "Jira",
            "Confluence",
            "Scrum",
            "Agile",
            "Microsoft Project",
            "Excel",
            "Team Management",
        ],
        "experience": [
            (
                "IT Project Manager",
                "ConsultingCorp",
                "2018-2026",
                "Managed Agile development teams. Project planning and tracking. Stakeholder coordination.",
            ),
            (
                "Product Owner",
                "SaaSCorp",
                "2015-2018",
                "Roadmap definition. Backlog management. Scrum ceremony facilitation.",
            ),
        ],
        "education": "MBA — IE Business School",
        "certifications": ["PMP", "PSM I"],
        "languages": ["Spanish (native)", "English C1"],
    },
    {
        "filename": "v2_jimena_ocana_data.pdf",
        "name": "Jimena Ocaña Vidal",
        "email": "jimena.ocana@email.com",
        "years": 4,
        "techs": [
            "Figma",
            "Sketch",
            "Adobe XD",
            "Photoshop",
            "Illustrator",
            "CSS",
            "HTML",
            "Basic JavaScript",
        ],
        "experience": [
            (
                "UX/UI Designer",
                "DesignStudio",
                "2022-2026",
                "User interface design with Figma. Interactive prototyping. User research and usability testing.",
            ),
            (
                "Junior Designer",
                "CreativeAgency",
                "2020-2022",
                "Graphic design and web layout. Visual asset creation.",
            ),
        ],
        "education": "BSc in Digital Design — Universidad de Barcelona",
        "certifications": ["Google UX Design Certificate"],
        "languages": ["Spanish (native)", "English B2"],
    },
]


def generate_pdf(profile: dict) -> bytes:
    pdf = FPDF()
    pdf.add_font(
        "DejaVu", "", "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf", uni=True
    )
    pdf.add_font(
        "DejaVu",
        "B",
        "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf",
        uni=True,
    )
    pdf.add_page()

    pdf.set_font("DejaVu", "B", 16)
    pdf.cell(0, 14, profile["name"], new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("DejaVu", "", 10)
    pdf.cell(0, 6, f"Email: {profile['email']}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(
        0, 6, f"Years of experience: {profile['years']}", new_x="LMARGIN", new_y="NEXT"
    )
    pdf.ln(4)

    pdf.set_font("DejaVu", "B", 13)
    pdf.cell(0, 10, "Technical Profile", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", "", 10)
    pdf.cell(0, 6, " | ".join(profile["techs"]), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.set_font("DejaVu", "B", 13)
    pdf.cell(0, 10, "Professional Experience", new_x="LMARGIN", new_y="NEXT")
    for role, company, years, desc in profile["experience"]:
        pdf.set_font("DejaVu", "B", 11)
        pdf.cell(0, 7, f"{role} — {company} ({years})", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("DejaVu", "", 10)
        pdf.multi_cell(0, 5, desc)
        pdf.ln(2)

    pdf.set_font("DejaVu", "B", 13)
    pdf.cell(0, 10, "Education", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", "", 10)
    pdf.cell(0, 6, profile["education"], new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    if profile["certifications"]:
        pdf.set_font("DejaVu", "B", 13)
        pdf.cell(0, 10, "Certifications", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("DejaVu", "", 10)
        for cert in profile["certifications"]:
            pdf.cell(0, 6, f"- {cert}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

    pdf.set_font("DejaVu", "B", 13)
    pdf.cell(0, 10, "Languages", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", "", 10)
    for lang in profile["languages"]:
        pdf.cell(0, 6, f"- {lang}", new_x="LMARGIN", new_y="NEXT")

    return pdf.output()


if __name__ == "__main__":
    print("=" * 72)
    print("GENERATING 10 TEST CVs (V2)")
    print("=" * 72)
    print()

    for p in profiles:
        path = os.path.join(OUTPUT_DIR, p["filename"])
        content = generate_pdf(p)
        with open(path, "wb") as f:
            f.write(content)
        size_kb = len(content) / 1024
        print(
            f"  {p['filename']:40s}  {p['name']:30s}  {p['years']} years  {len(p['techs'])} techs  ({size_kb:.1f} KB)"
        )

    print(f"\nGenerated {len(profiles)} PDFs in ./{OUTPUT_DIR}/")
    print()
    print("STEPS FOR TESTING WITH THE NEW OFFER:")
    print("  1. Start the server: python main.py")
    print("  2. Open http://localhost:8000")
    print("  3. Go to the 'Offers' tab")
    print("  4. Read the offer from data/offers/oferta_ejemplo.txt")
    print("  5. Create a new offer with title 'Senior Data Engineer'")
    print("  6. Paste the offer text into the description")
    print("  7. Upload the 10 generated CVs (v2_*)")
    print("  8. Wait for processing and review the ranking")
