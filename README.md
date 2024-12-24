# Gitcoin Grants Data Dashboard

## Overview
This project is a dashboard for visualizing Gitcoin Grants data. It provides real-time analytics and insights into Gitcoin's grant programs, funding rounds, and community participation.

## Architecture
- **Frontend**: Streamlit web application
- **Database**: PostgreSQL (via Regendata's Grants DB)
- **Visualization**: Plotly for interactive charts

## Data Sources
- **Primary**: Gitcoin Indexer PostgreSQL Database
- **Update Frequency**: Real-time sync with blockchain events
- **Data Types**:
  - Grant metadata
  - Contribution history
  - Donor information
  - Round statistics

## Contributing
We welcome contributions! Please follow these steps:
1. Fork the repository
2. Create a new branch (`git checkout -b feature-branch`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature-branch`)
5. Open a pull request

## License
This project is licensed under the Apache License. See the [LICENSE](LICENSE) file for details.

## Contact
For any questions or suggestions, please open an issue